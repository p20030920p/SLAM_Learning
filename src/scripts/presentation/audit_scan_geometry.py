"""Read actual ROS bag scans to audit the geometric pressure test."""
import json
import sys
from pathlib import Path

import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import LaserScan

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
from slam_learning.core.scan_geometry import normal_coverage


def main():
    run = Path(sys.argv[1])
    events = [json.loads(line) for line in (run / "scan-stress.jsonl").read_text().splitlines()]
    restore = min(event["stamp_s"] for event in events if event["phase"] == "restored")
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(run / "input-bag"), storage_id="mcap"), rosbag2_py.ConverterOptions("", ""))
    ratios = {"full_before": [], "limited": [], "full_after": [], "restored": []}
    frames = {key: 0 for key in ratios}
    while reader.has_next():
        topic, data, _ = reader.read_next()
        if topic not in ("/scan", "/scan_degraded"):
            continue
        scan = deserialize_message(data, LaserScan)
        stamp = scan.header.stamp.sec+scan.header.stamp.nanosec*1e-9
        key = ("full_before" if stamp < restore else "full_after") if topic == "/scan" else ("limited" if stamp < restore else "restored")
        frames[key] += 1
        metric = normal_coverage(scan.ranges, scan.angle_min, scan.angle_increment, scan.range_min, scan.range_max)
        if metric:
            ratios[key].append(metric["ratio"])
    result = {key: {"scan_frames": frames[key], "usable_normal_frames": len(value), "median_normal_ratio": float(np.median(value)) if value else None} for key, value in ratios.items()}
    result["scope"] = "Measured normal-coverage diagnostic; not a calibrated observability or recovery probability"
    (run / "geometry-audit.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
