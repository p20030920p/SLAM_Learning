"""Only mapping A may read provided poses. Record real lidar/depth returns and TF."""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformListener

from observe_session import matrix, seconds


def main():
    run, truth_path = map(Path, sys.argv[1:3])
    rclpy.init()
    node = rclpy.create_node("probe_mapping_A_provided_poses")
    node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
    tf = Buffer()
    listener = TransformListener(tf, node)
    pending, truth = deque(), deque(maxlen=30000)
    last, records = {}, []
    archive = {}
    stream = truth_path.open()

    def receive(msg, kind):
        stamp = seconds(msg.header.stamp)
        if stamp - last.get(kind, -1e9) >= .8:
            pending.append((kind, msg))
            last[kind] = stamp

    node.create_subscription(LaserScan, "/scan", lambda msg: receive(msg, "lidar2d"), qos_profile_sensor_data)
    node.create_subscription(PointCloud2, "/depth/points", lambda msg: receive(msg, "depth"), qos_profile_sensor_data)
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=.03)
            while True:
                location = stream.tell()
                line = stream.readline()
                if not line.endswith("\n"):
                    stream.seek(location)
                    break
                truth.append(json.loads(line))
            for _ in range(len(pending)):
                kind, msg = pending.popleft()
                stamp = seconds(msg.header.stamp)
                if not truth or stamp > truth[-1]["stamp_s"]:
                    pending.append((kind, msg))
                    continue
                near = min(truth, key=lambda row: abs(row["stamp_s"] - stamp))
                if abs(near["stamp_s"] - stamp) > .05:
                    continue
                try:
                    extrinsic = tf.lookup_transform("base_footprint", msg.header.frame_id, rclpy.time.Time()).transform
                except Exception:
                    pending.append((kind, msg))
                    continue
                if kind == "lidar2d":
                    ranges = np.asarray(msg.ranges)
                    angles = msg.angle_min + np.arange(len(ranges)) * msg.angle_increment
                    valid = np.isfinite(ranges) & (ranges > .45) & (ranges < 12)
                    points = np.column_stack((ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid]), np.zeros(valid.sum())))
                else:
                    points = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True).reshape(-1, 3)[::12]
                    distance = np.linalg.norm(points, axis=1)
                    points = points[np.isfinite(points).all(axis=1) & (distance > .25) & (distance < 4.01)]
                p, q = extrinsic.translation, extrinsic.rotation
                pose = matrix(near["xyz"], near["xyzw"]) @ matrix([p.x, p.y, p.z], [q.x, q.y, q.z, q.w])
                key = f"{kind}_{len(records):05d}"
                archive[key] = points.astype(np.float32)
                archive[key + "_pose"] = pose
                records.append({"key": key, "stamp_s": stamp, "frame_id": msg.header.frame_id,
                                "truth_delta_s": abs(near["stamp_s"] - stamp), "points": len(points)})
            if (run / "finished.json").exists() or (run / "STOP").exists():
                break
    finally:
        np.savez_compressed(run / "probe-mapping-inputs.npz", **archive)
        (run / "probe-mapping-inputs.json").write_text(json.dumps({"scope": "real sensor returns; mapping A provided poses only", "records": records}, indent=2) + "\n")
        print(f"Saved {len(records)} actual lidar/depth frames", flush=True)
        stream.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        del listener


if __name__ == "__main__":
    main()
