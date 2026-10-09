"""Verify ROS serialized bytes and measure data-setter overhead on this host.

Deterministic synthetic payloads only; not a sensor or algorithm benchmark.
Run with WSL Python after sourcing ROS Humble.
"""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from rclpy.serialization import serialize_message, deserialize_message
from sensor_msgs.msg import Image, PointCloud2, PointField


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    record = {"scope": "Synthetic message data-setter microbenchmark; no sensor/SLAM performance claim",
              "status": "failed", "cases": []}
    try:
        for kind, shape, dtype, encoding in (("mono", (480, 640), "u1", "mono8"),
                ("rgb", (480, 640, 3), "u1", "bgr8"),
                ("depth", (480, 640), "<f4", "32FC1"),
                ("cloud", (180000, 4), "<f4", None)):
            values = (np.arange(np.prod(shape), dtype=np.uint32) % 251).astype(dtype).reshape(shape)
            payload = values.tobytes()
            old, new = (PointCloud2(), PointCloud2()) if kind == "cloud" else (Image(), Image())
            for message in (old, new):
                message.header.frame_id = "synthetic_payload_check"
                if kind == "cloud":
                    message.height = 1
                    message.width = shape[0]
                    message.point_step = 16
                    message.row_step = 16 * shape[0]
                    message.fields = [PointField(name=name, offset=i*4, datatype=PointField.FLOAT32, count=1)
                                      for i, name in enumerate(("x", "y", "z", "intensity"))]
                else:
                    message.height, message.width = shape[:2]
                    message.encoding = encoding
                    message.step = values.strides[0]
            old.data = payload
            new.data = array("B", payload)
            a, b = serialize_message(old), serialize_message(new)
            # Compare all decoded fields and payload, rather than unspecified
            # CDR alignment padding bytes in the outer serialized envelope.
            decoded_old = deserialize_message(a, type(old))
            decoded_new = deserialize_message(b, type(new))
            if old != new or decoded_old != decoded_new or bytes(decoded_new.data) != payload:
                raise ValueError(f"ROS decoded message or payload mismatch: {kind}")
            timings = {}
            for label, message, use_array in (("bytes", old, False), ("typed_array", new, True)):
                durations = []
                for _ in range(5):
                    start = time.perf_counter()
                    message.data = array("B", payload) if use_array else payload
                    durations.append((time.perf_counter() - start) * 1000)
                timings[label] = {"median_ms": float(np.median(durations)), "max_ms": max(durations)}
            record["cases"].append({"case": kind, "payload_bytes": len(payload),
                "deserialized_fields_identical": True, "payload_identical": True,
                "cdr_bytes_equal_in_this_call": a == b, "serialized_sha256": hashlib.sha256(a).hexdigest(),
                "setter_timings": timings})
        record["status"] = "passed"
    except Exception as error:
        record["error"] = repr(error)
    (args.output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))
    return int(record["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
