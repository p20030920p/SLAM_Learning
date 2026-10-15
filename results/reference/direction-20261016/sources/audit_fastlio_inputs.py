"""Verify serialized inputs actually recorded in the native ROS2 bag."""

import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import PointCloud2, Imu
from sensor_msgs_py import point_cloud2


def audit(run, output):
    reader = rosbag2_py.SequentialReader()
    reader.open(
        rosbag2_py.StorageOptions(uri=str(run / "input-bag"), storage_id="mcap"),
        rosbag2_py.ConverterOptions("", ""),
    )
    reader.set_filter(rosbag2_py.StorageFilter(topics=["/study/rolling", "/study/imu"]))
    clouds = []
    imu = []
    minimum_points = 10**9
    while reader.has_next():
        topic, data, _ = reader.read_next()
        msg = deserialize_message(data, PointCloud2 if topic == "/study/rolling" else Imu)
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if topic == "/study/rolling":
            a = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z", "time"), skip_nans=False)
            assert np.isfinite(a).all(), f"Nonfinite point input at {stamp}"
            assert np.min(a[:, 3]) >= 0 and 0.19 <= np.max(a[:, 3]) <= 0.31
            assert np.all(np.diff(a[:, 3]) >= 0)
            minimum_points = min(minimum_points, len(a))
            clouds.append(stamp)
        elif stamp >= 3:
            assert np.isfinite(
                [
                    msg.linear_acceleration.x,
                    msg.linear_acceleration.y,
                    msg.linear_acceleration.z,
                    msg.angular_velocity.x,
                    msg.angular_velocity.y,
                    msg.angular_velocity.z,
                ]
            ).all()
            imu.append(stamp)
    assert len(clouds) > 100 and len(imu) > 5000
    assert np.all(np.diff(clouds) > 0) and np.all(np.diff(imu) > 0)
    report = {
        "schema_version": 1,
        "kind": "serialized_fastlio_input_audit",
        "status": "executed",
        "exit_code": 0,
        "rolling_cloud_messages": len(clouds),
        "finite_point_fields": True,
        "nonnegative_ordered_point_times": True,
        "minimum_cloud_points": minimum_points,
        "median_scan_interval_s": float(np.median(np.diff(clouds))),
        "imu_after_settling_messages": len(imu),
        "median_imu_interval_s": float(np.median(np.diff(imu))),
        "scope": "Checks recorded rolling clouds and source IMU after t>=3s settling gate; no truth read",
        "bags": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (run / "input-bag").glob("*.mcap")
        },
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
