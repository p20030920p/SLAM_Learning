"""Read-only image and stereo geometry screening after an incident.

Stored calibration equality and scene matches cannot establish metrology accuracy.
General fundamental-matrix RANSAC does not impose horizontal epipolar lines.
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("capture", type=Path)
    ap.add_argument("--stereo", type=Path, required=True)
    ap.add_argument("--reference-capture", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    capture = json.loads((args.capture / "capture.json").read_text())
    reference = json.loads(args.reference_capture.read_text())
    stereo = json.loads((args.stereo / "stereo.json").read_text())
    if stereo["source_sha256"] != capture["raw"]["sha256"] or stereo["status"] != "exported":
        raise ValueError("Stereo export does not match the capture")
    for row in stereo["pairs"]:
        for side in ("left", "right"):
            path = args.stereo / row[side]
            row[side + "_image_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    result = {"scope": "Scene-dependent basic health screening, not a certified damage or range-accuracy test",
              "raw_sha256": capture["raw"]["sha256"], "device": capture["device"],
              "stored_intrinsics_unchanged": capture["intrinsics"] == reference["intrinsics"],
              "stored_extrinsics_unchanged": capture["extrinsics_to_depth"] == reference["extrinsics_to_depth"],
              "streams": capture["streams"], "images": {}, "stereo_pairs": []}
    frames = json.loads((args.capture / "frames.json").read_text())
    first_receipt = min(r[2] for samples in frames.values() for r in samples)
    begin = capture.get("host_capture_start_monotonic_ns", int(first_receipt * 1e9)) / 1e9 + 2
    result["steady_streams"] = {}
    for key, samples in frames.items():
        unique = {}
        for row in samples:
            unique.setdefault(row[0], row)
        rows = np.asarray([r[:3] for r in unique.values() if r[2] >= begin])
        if len(rows) < 2:
            raise ValueError(f"Insufficient post-warmup frames: {key}")
        result["steady_streams"][key] = {"warmup_s": 2, "unique_frames": len(rows),
            "sensor_hz": 1000 * (len(rows)-1) / (rows[-1, 1]-rows[0, 1]),
            "max_sensor_gap_ms": float(np.diff(rows[:, 1]).max()),
            "max_host_receipt_gap_ms": float(np.diff(rows[:, 2]).max()*1000)}
    for filename in ("color.png", "ir1.png", "ir2.png"):
        image = cv2.imread(str(args.capture / filename), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(filename)
        result["images"][filename] = {"sample": "First saved preview after two seconds, not whole-recording statistics",
            "mean_8bit": float(image.mean()), "std_8bit": float(image.std()),
            "fraction_below_10": float((image < 10).mean()), "fraction_above_250": float((image > 250).mean())}
    sift = cv2.SIFT_create(nfeatures=4000)
    matcher = cv2.BFMatcher(cv2.NORM_L2)
    all_dy = []
    cv2.setRNGSeed(19)
    for row in stereo["pairs"]:
        left = cv2.imread(str(args.stereo / row["left"]), 0)
        right = cv2.imread(str(args.stereo / row["right"]), 0)
        kp1, d1 = sift.detectAndCompute(left, None)
        kp2, d2 = sift.detectAndCompute(right, None)
        summary = {"index": row["index"], "left_frame": row["left_frame"], "left_features": len(kp1), "right_features": len(kp2),
                   "right_minus_left_s": row["right_minus_left_s"],
                   "left_image_sha256": row["left_image_sha256"], "right_image_sha256": row["right_image_sha256"]}
        if d1 is None or d2 is None or min(len(d1), len(d2)) < 8:
            summary["status"] = "insufficient_features"
            result["stereo_pairs"].append(summary)
            continue
        forward = [m for pair in matcher.knnMatch(d1, d2, k=2) if len(pair) == 2 for m, n in [pair] if m.distance < 0.7 * n.distance]
        reverse = {m.queryIdx: m.trainIdx for pair in matcher.knnMatch(d2, d1, k=2) if len(pair) == 2 for m, n in [pair] if m.distance < 0.7 * n.distance}
        matches = [m for m in forward if reverse.get(m.trainIdx) == m.queryIdx]
        summary["mutual_ratio_matches"] = len(matches)
        if len(matches) < 8:
            summary["status"] = "insufficient_matches"
            result["stereo_pairs"].append(summary)
            continue
        a = np.float32([kp1[m.queryIdx].pt for m in matches])
        b = np.float32([kp2[m.trainIdx].pt for m in matches])
        _, mask = cv2.findFundamentalMat(a, b, cv2.FM_RANSAC, 1.0, 0.999)
        if mask is None:
            summary["status"] = "fundamental_estimation_failed"
            result["stereo_pairs"].append(summary)
            continue
        keep = mask.ravel().astype(bool)
        dy = b[keep, 1] - a[keep, 1]
        dx = a[keep, 0] - b[keep, 0]
        summary.update(status="measured", geometric_inliers=int(keep.sum()),
            absolute_vertical_disparity_median_px=float(np.median(np.abs(dy))),
            absolute_vertical_disparity_p95_px=float(np.percentile(np.abs(dy), 95)),
            signed_vertical_disparity_median_px=float(np.median(dy)),
            positive_horizontal_disparity_fraction=float((dx > 0).mean()))
        all_dy.extend(np.abs(dy).tolist())
        if not (args.output / "stereo-matches.png").exists():
            shown = [m for m, ok in zip(matches, keep) if ok][:70]
            canvas = cv2.drawMatches(left, kp1, right, kp2, shown, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            for y in range(40, 480, 40):
                cv2.line(canvas, (0, y), (1279, y), (0, 170, 0), 1)
            cv2.imwrite(str(args.output / "stereo-matches.png"), canvas)
        result["stereo_pairs"].append(summary)
    result["geometry_summary"] = {"sampled_pairs": len(stereo["pairs"]), "inlier_matches": len(all_dy),
        "absolute_vertical_disparity_median_px": float(np.median(all_dy)) if all_dy else None,
        "absolute_vertical_disparity_p95_px": float(np.percentile(all_dy, 95)) if all_dy else None,
        "interpretation": "Screening only: repeated IR dots, saturation, coplanar objects and match selection limit confidence. No automatic calibration write."}
    (args.output / "health.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "stereo_pairs"}, indent=2))


if __name__ == "__main__":
    main()
