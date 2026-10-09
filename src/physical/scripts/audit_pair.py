"""Associate same-host receipt times; never claim exposure/firing synchronization."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def nearest(reference, query):
    """Return nearest reference index, preferring the earlier item on ties."""
    right = np.searchsorted(reference, query).clip(0, len(reference) - 1)
    left = (right - 1).clip(0, len(reference) - 1)
    return np.where(np.abs(reference[left] - query) <= np.abs(reference[right] - query), left, right)


def distribution(values):
    return {"count": len(values), "median_ms": float(np.median(values)),
            "p95_ms": float(np.percentile(values, 95)), "max_ms": float(np.max(values))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("session", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--skip-seconds", type=float, default=2)
    args = ap.parse_args()
    if args.output.exists() or args.skip_seconds < 0:
        ap.error("Use a new output directory and a nonnegative warmup")
    camera = json.loads((args.session / "camera/capture.json").read_text())
    lidar = json.loads((args.session / "l2/capture.json").read_text())
    for manifest in (camera, lidar):
        clock = manifest.get("host_clock", {})
        if clock.get("name") != "perf_counter" or "QueryPerformanceCounter" not in clock.get("implementation", ""):
            raise ValueError("Requires the Windows high-resolution, system-wide receipt clock; do not mix older recordings")
        if manifest["status"] != "received":
            raise ValueError("Both captures must have received data")
    for path, expected in ((args.session / "camera/raw.db3", camera["raw"]["sha256"]),
                           (args.session / "l2/uart.bin", lidar["raw_sha256"])):
        with path.open("rb") as raw:
            if hashlib.file_digest(raw, "sha256").hexdigest() != expected:
                raise ValueError(f"Raw hash mismatch: {path}")
    frames = json.loads((args.session / "camera/frames.json").read_text())
    rows = list(csv.DictReader((args.session / "l2/packets-102.csv").open()))
    stamps = np.asarray([int(r["host_receive_monotonic_ns"]) for r in rows], dtype=np.int64)
    if not len(stamps) or (np.diff(stamps) < 0).any():
        raise ValueError("L2 receipt times must be nondecreasing")
    begin = max(camera["host_capture_start_monotonic_ns"], lidar["host_capture_start_monotonic_ns"]) + int(args.skip_seconds * 1e9)
    end = min(max(int(round(r[2] * 1e9)) for r in frames["stream.depth:0"]), int(stamps[-1]))
    if end <= begin:
        raise ValueError("No usable common recording interval")
    result = {"scope": "Same Windows host receipt-time association; no hardware sync, calibrated extrinsics, deskew, or fused pose",
              "session": str(args.session.resolve()), "status": "associated", "warmup_seconds": args.skip_seconds,
              "overlap_seconds": (end - begin) / 1e9, "camera_raw_sha256": camera["raw"]["sha256"],
              "lidar_raw_sha256": lidar["raw_sha256"], "clock": camera["host_clock"], "streams": {}}
    exported = []
    # 50 consecutive lines are an algorithm input group, not a complete revolution.
    group_stamps = stamps[49::50]
    if not len(group_stamps):
        raise ValueError("Need at least 50 L2 lines for the group diagnostic")
    args.output.mkdir(parents=True)
    for key, samples in frames.items():
        unique = {}
        for row in samples:
            unique.setdefault(row[0], row)
        selected = [(n, int(round(r[2] * 1e9))) for n, r in unique.items() if begin <= int(round(r[2] * 1e9)) <= end]
        if not selected:
            raise ValueError(f"No camera frames in overlap: {key}")
        camera_times = np.asarray([r[1] for r in selected], dtype=np.int64)
        indices = nearest(stamps, camera_times)
        offsets_ms = (stamps[indices] - camera_times) / 1e6
        group_indices = nearest(group_stamps, camera_times)
        result["streams"][key] = {"unique_frames_in_overlap": len(selected),
            "host_receipt_hz": (len(selected) - 1) * 1e9 / (camera_times[-1] - camera_times[0]),
            "nearest_line_abs_offset": distribution(np.abs(offsets_ms)),
            "nearest_50line_group_abs_offset": distribution(np.abs(group_stamps[group_indices] - camera_times) / 1e6)}
        for (number, stamp), index, offset in zip(selected, indices, offsets_ms):
            exported.append([key, number, stamp, int(index), int(rows[index]["seq"]), int(stamps[index]), float(offset)])
    with (args.output / "receipt-associations.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["camera_stream", "frame_number", "camera_host_ns", "lidar_line_index", "lidar_sequence", "lidar_host_ns", "lidar_minus_camera_ms"])
        writer.writerows(exported)
    (args.output / "association.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
