"""Publish only newly emitted author-execution snapshots to the actual RViz window."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path as RosPath
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py.point_cloud2 import create_cloud_xyz32
from std_msgs.msg import Header
from visualization_msgs.msg import Marker


def main():
    run, method = Path(sys.argv[1]), sys.argv[2]
    rclpy.init()
    node = rclpy.create_node("author_live_snapshot_bridge")
    publishers = {name: node.create_publisher(PointCloud2, "/author/"+name, 5)
                  for name in ("map", "removed", "input", "particles")}
    path_pub = node.create_publisher(RosPath, "/author/path", 5)
    truth_pub = node.create_publisher(RosPath, "/author/truth", 5)
    label_pub = node.create_publisher(Marker, "/author/status", 5)
    estimate, truth = RosPath(), RosPath()
    estimate.header.frame_id = truth.header.frame_id = "author_map"
    last, current = -1, None
    log = (run / "live-published.jsonl").open("w")
    (run / "viewer-ready.json").write_text(json.dumps({"method": method, "mode": "new snapshots only; no old results loaded"}))
    try:
        while rclpy.ok() and not (run / "viewer-stop").exists():
            latest = run / "live/latest.json"
            if latest.exists():
                event = json.loads(latest.read_text())
                if event["method"] != method:
                    raise ValueError("Method label does not match native snapshot")
                if event["serial"] != last:
                    current = dict(np.load(run / "live" / event["file"], allow_pickle=False))
                    last = event["serial"]
                    log.write(json.dumps({**event, "published_unix": time.time(), "published_monotonic_s": time.monotonic()})+"\n")
                    log.flush()
                    if "pose" in current:
                        for target, values in ((estimate, current["pose"]), (truth, current["truth"])):
                            point = PoseStamped()
                            point.header.frame_id = "author_map"
                            point.pose.position.x, point.pose.position.y = float(values[0]), float(values[1])
                            point.pose.orientation.w = 1.0
                            target.poses.append(point)
            if current is not None:
                header = Header(frame_id="author_map", stamp=node.get_clock().now().to_msg())
                for name, publisher in publishers.items():
                    points = current.get(name, np.empty((0, 3)))
                    if name == "particles" and len(points):
                        points = np.column_stack([points[:, :2], np.zeros(len(points))])
                    publisher.publish(create_cloud_xyz32(header, np.asarray(points, dtype=np.float32)))
                for publisher, path in ((path_pub, estimate), (truth_pub, truth)):
                    path.header.stamp = header.stamp
                    publisher.publish(path)
                label = Marker()
                label.header, label.type, label.action = header, Marker.TEXT_VIEW_FACING, Marker.ADD
                label.id, label.pose.orientation.w = 0, 1.0
                label.pose.position.x, label.pose.position.y = (0.0, 5.0) if method == "ir-mcl" else (10.0, 35.0)
                label.scale.z, label.color.r, label.color.g, label.color.b, label.color.a = 1.0, 1.0, 1.0, 1.0, 1.0
                label.text = f"LIVE {method} | native frame {event['frame']}\n{event['phase']}"
                label_pub.publish(label)
            rclpy.spin_once(node, timeout_sec=.10)
    finally:
        log.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
