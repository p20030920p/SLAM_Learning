"""Record raw D435i streams with librealsense; never label capture as a scientific result."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--session", required=True, help="Physical protocol session label")
    parser.add_argument("--output", type=Path, default=Path(".cache/hardware"))
    args = parser.parse_args()
    if args.seconds <= 0 or not args.session.replace("-", "").replace("_", "").isalnum():
        parser.error("Positive duration and a simple session label are required")
    output = args.output / f"{args.session}-{uuid.uuid4().hex[:8]}"
    output.mkdir(parents=True, exist_ok=False)
    record = {"schema_version": 1, "kind": "physical_sensor_capture", "sensor": "D435i",
              "session": args.session, "status": "recording", "evaluation_completed": False,
              "started_at": datetime.now(timezone.utc).isoformat(), "requested_seconds": args.seconds,
              "scope": "Raw RGB, depth, accelerometer and gyroscope. No SLAM pose or hardware-test score claimed."}
    pipeline = None
    started = False
    try:
        import pyrealsense2 as rs
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.accel)
        config.enable_stream(rs.stream.gyro)
        config.enable_record_to_file(str(output / "capture.bag"))
        profile = pipeline.start(config)
        started = True
        device = profile.get_device()
        record["device_name"] = device.get_info(rs.camera_info.name)
        record["firmware"] = device.get_info(rs.camera_info.firmware_version)
        record["sdk_version"] = getattr(rs, "__version__", "Unavailable; record installed package version separately")
        record["depth_scale_m"] = device.first_depth_sensor().get_depth_scale()
        record["profiles"] = [{"stream": str(p.stream_type()), "format": str(p.format()), "fps": p.fps()}
                              for p in profile.get_streams()]
        record["intrinsics"] = {}
        for stream in (rs.stream.color, rs.stream.depth):
            intrinsic = profile.get_stream(stream).as_video_stream_profile().get_intrinsics()
            record["intrinsics"][str(stream)] = {key: getattr(intrinsic, key)
                for key in ("width", "height", "fx", "fy", "ppx", "ppy", "coeffs")}
        extrinsic = profile.get_stream(rs.stream.depth).get_extrinsics_to(profile.get_stream(rs.stream.color))
        record["depth_to_color"] = {"rotation": extrinsic.rotation, "translation_m": extrinsic.translation}
        end = time.monotonic() + args.seconds
        samples = []
        while time.monotonic() < end:
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            for frame in frames:
                samples.append({"stream": str(frame.get_profile().stream_type()), "frame_number": frame.get_frame_number(),
                                "sensor_timestamp_ms": frame.get_timestamp(), "domain": str(frame.get_frame_timestamp_domain()),
                                "host_monotonic_s": time.monotonic()})
        record["status"] = "recorded"
        (output / "received_frames.json").write_text(json.dumps(samples, indent=2) + "\n")
        record["timestamp_note"] = "Delivery samples are not a complete IMU-rate audit; verify raw bag streams on playback. No cross-sensor clock synchronization assumed."
    except Exception as error:
        record.update(status="failed", error=str(error), traceback=traceback.format_exc())
    finally:
        if started:
            pipeline.stop()
        bag = output / "capture.bag"
        if bag.exists():
            h = hashlib.sha256()
            with bag.open("rb") as stream:
                for block in iter(lambda: stream.read(4*1024*1024), b""):
                    h.update(block)
            record["raw_bag"] = {"sha256": h.hexdigest(), "bytes": bag.stat().st_size, "availability": "local_only"}
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        (output / "capture.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(output / "capture.json")
    return int(record["status"] != "recorded")


if __name__ == "__main__":
    raise SystemExit(main())
