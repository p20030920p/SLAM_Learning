"""Export real, SDK-aligned RGB-D for frozen-camera semantic input checks.

Replica is only the author loader's file layout, never the provenance of images.
Original RGB PNGs and a separate JPEG compatibility view are both retained.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import traceback

import cv2
import numpy as np
import pyrealsense2 as rs


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def calibration(profile):
    value = profile.as_video_stream_profile().get_intrinsics()
    return {k: getattr(value, k) for k in
            ("width", "height", "fx", "fy", "ppx", "ppy", "coeffs")} | {"model": str(value.model)}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("recording", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--fixed-sensor-session", action="store_true")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--skip-seconds", type=float, default=3)
    ap.add_argument("--interval", type=float, default=1)
    ap.add_argument("--max-skew-ms", type=float, default=25)
    args = ap.parse_args()
    if not args.fixed_sensor_session:
        ap.error("Identity poses require explicit --fixed-sensor-session acknowledgement")
    if args.frames < 1 or args.skip_seconds < 0 or args.interval <= 0 or args.max_skew_ms <= 0:
        ap.error("Invalid sampling options")
    note_path = args.recording.parent / "session-note.json"
    note = json.loads(note_path.read_text(encoding="utf-8"))
    if note.get("camera_fixed_declared_by_operator") is not True:
        ap.error("Source session-note.json must contain the operator's fixed camera declaration")
    args.output.mkdir(parents=True, exist_ok=False)
    results = args.output / "replica-layout/physical/results"
    results.mkdir(parents=True)
    (args.output / "rgb").mkdir()
    record = {"schema_version": 1, "kind": "physical_rgbd_input", "status": "failed",
              "started_at": datetime.now(timezone.utc).isoformat(),
              "source_recording": str(args.recording.resolve()), "source_session_note": note,
              "script_sha256": sha(__file__), "sdk": importlib.metadata.version("pyrealsense2"),
              "pose_source": "Identity T_world_color from operator-declared fixed camera; not odometry or independent GT",
              "world_frame": "First color optical frame: +x right, +y down, +z forward; meters",
              "alignment": "rs.align(rs.stream.color); no temporal/spatial/hole-filling filters",
              "timestamp_policy": "Native stream times; SDK association, not hardware synchronization",
              "replica_note": "File layout compatibility only; observations are physical RealSense data",
              "jpeg_quality": 95, "original_rgb_png_retained": True,
              "sampling": {"frames": args.frames, "skip_seconds": args.skip_seconds,
                           "interval_s": args.interval, "max_skew_ms": args.max_skew_ms},
              "semantic_algorithm_executed": False, "quality_metrics_evaluated": False,
              "frames": [], "skew_rejected": 0}
    pipeline = rs.pipeline()
    started = False
    try:
        record["source_sha256"] = sha(args.recording)
        capture = json.loads((args.recording.parent / "capture.json").read_text(encoding="utf-8"))
        if record["source_sha256"] != capture["raw"]["sha256"]:
            raise ValueError("Raw recording differs from capture hash")
        record["device"] = capture.get("device")
        config = rs.config()
        config.enable_device_from_file(str(args.recording.resolve()), repeat_playback=False)
        profile = pipeline.start(config)
        started = True
        playback = profile.get_device().as_playback()
        playback.set_real_time(False)
        color_profile = profile.get_stream(rs.stream.color)
        depth_profile = profile.get_stream(rs.stream.depth)
        intr = calibration(color_profile)
        if any(abs(c) > 1e-7 for c in intr["coeffs"]):
            raise ValueError("Nonzero color distortion requires an explicit undistortion adapter")
        unit = profile.get_device().first_depth_sensor().get_depth_scale()
        ext = depth_profile.get_extrinsics_to(color_profile)
        record.update(color_intrinsics=intr, raw_depth_intrinsics=calibration(depth_profile),
                      depth_unit_m=unit, depth_aligned_to="color",
                      sdk_depth_to_color={"rotation_column_major": ext.rotation, "translation_m": ext.translation})
        align = rs.align(rs.stream.color)
        first = None
        seen_color, seen_depth = set(), set()
        deadline = time.monotonic() + 180
        while len(record["frames"]) < args.frames and time.monotonic() < deadline:
            try:
                frameset = pipeline.wait_for_frames(2000)
            except RuntimeError:
                if playback.current_status() == rs.playback_status.stopped:
                    break
                raise
            color, depth = frameset.get_color_frame(), frameset.get_depth_frame()
            if not color or not depth:
                continue
            stamp = color.get_timestamp() / 1000
            if first is None:
                first = stamp
            index = len(record["frames"])
            if stamp - first < args.skip_seconds + index * args.interval:
                continue
            if color.get_frame_number() in seen_color or depth.get_frame_number() in seen_depth:
                continue
            if color.get_frame_timestamp_domain() != depth.get_frame_timestamp_domain():
                raise ValueError("RGB and depth have different timestamp domains")
            skew = depth.get_timestamp() - color.get_timestamp()
            if abs(skew) > args.max_skew_ms:
                record["skew_rejected"] += 1
                continue
            aligned = align.process(frameset).get_depth_frame()
            color_data = np.asanyarray(color.get_data())
            if color.profile.format() == rs.format.rgb8:
                bgr = cv2.cvtColor(color_data, cv2.COLOR_RGB2BGR)
            elif color.profile.format() == rs.format.bgr8:
                bgr = color_data
            else:
                raise ValueError(f"Unsupported recorded color format: {color.profile.format()}")
            depth_data = np.asanyarray(aligned.get_data())
            if depth_data.dtype != np.uint16 or depth_data.shape != bgr.shape[:2]:
                raise ValueError("Aligned depth must be uint16 at RGB resolution")
            aligned_intr = calibration(aligned.profile)
            if any(abs(aligned_intr[k] - intr[k]) > 1e-5 for k in ("fx", "fy", "ppx", "ppy", "width", "height")):
                raise ValueError("Aligned depth calibration differs from target color")
            paths = {"rgb_png": Path("rgb") / f"{index:06d}.png",
                     "color": Path("replica-layout/physical/results") / f"frame{index:06d}.jpg",
                     "depth": Path("replica-layout/physical/results") / f"depth{index:06d}.png"}
            for key, path in paths.items():
                data = depth_data if key == "depth" else bgr
                options = [cv2.IMWRITE_JPEG_QUALITY, 95] if key == "color" else []
                if not cv2.imwrite(str(args.output / path), data, options):
                    raise OSError(path)
            valid = depth_data[depth_data > 0].astype(float) * unit
            row = {"index": index, "elapsed_s": stamp - first, "color_stamp_s": stamp,
                   "depth_stamp_s": depth.get_timestamp() / 1000, "depth_minus_color_ms": skew,
                   "color_frame": color.get_frame_number(), "depth_frame": depth.get_frame_number(),
                   "timestamp_domain": str(color.get_frame_timestamp_domain()),
                   "valid_depth_fraction": float(np.count_nonzero(depth_data) / depth_data.size),
                   "nonzero_depth_median_m": float(np.median(valid)) if len(valid) else None,
                   "T_world_color": np.eye(4).tolist(),
                   "files": {key: {"path": path.as_posix(), "sha256": sha(args.output / path)}
                             for key, path in paths.items()}}
            record["frames"].append(row)
            seen_color.add(row["color_frame"])
            seen_depth.add(row["depth_frame"])
        if len(record["frames"]) != args.frames:
            raise ValueError(f"Only exported {len(record['frames'])}/{args.frames} requested frames")
        camera = {"w": intr["width"], "h": intr["height"], "fx": intr["fx"], "fy": intr["fy"],
                  "cx": intr["ppx"], "cy": intr["ppy"], "scale": 1 / unit}
        (args.output / "replica-layout/cam_params.json").write_text(json.dumps({"camera": camera}, indent=2) + "\n", encoding="utf-8")
        # JSON is valid YAML, which the native ConceptGraphs loader accepts.
        cfg = {"dataset_name": "replica", "camera_params": {"image_height": intr["height"],
               "image_width": intr["width"], "fx": intr["fx"], "fy": intr["fy"], "cx": intr["ppx"],
               "cy": intr["ppy"], "png_depth_scale": 1 / unit}}
        (args.output / "conceptgraphs-camera.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        (results.parent / "traj.txt").write_text((" ".join(map(str, np.eye(4).ravel())) + "\n") * args.frames, encoding="utf-8")
        record["configuration_files"] = {str(p.relative_to(args.output)).replace("\\", "/"): sha(p)
            for p in (args.output / "replica-layout/cam_params.json", args.output / "conceptgraphs-camera.json", results.parent / "traj.txt")}
        record["status"] = "exported"
    except Exception as error:
        record.update(error=repr(error), traceback=traceback.format_exc())
    finally:
        if started:
            pipeline.stop()
        (args.output / "rgbd.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in record.items() if k != "frames"}, indent=2))
    print(f"frames={len(record['frames'])}")
    return int(record["status"] != "exported")


if __name__ == "__main__":
    raise SystemExit(main())
