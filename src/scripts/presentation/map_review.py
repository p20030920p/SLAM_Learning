"""Real RViz display of measured 3D map-cleaning results, explicitly a result review."""
import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import rclpy
import yaml
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    data = np.load(args.audit / "point-label-inputs.npz", allow_pickle=False)
    masks = np.load(args.audit / "baseline/retention-masks.npz", allow_pickle=False)
    metrics = json.loads((args.audit / "record.json").read_text())["configurations"]["baseline"]["metrics"]
    points, labels = data["points"], data["labels"]
    rclpy.init()
    node = rclpy.create_node("measured_3d_map_review")
    qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE)
    pubs, messages = [], []
    for method in ("raw", "dufomap", "beautymap"):
        selected = np.flatnonzero(masks[method])[::6]
        structured = np.zeros(len(selected), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("rgb", "<u4")])
        for index, axis in enumerate(("x", "y", "z")):
            structured[axis] = points[selected, index]
        structured["rgb"] = np.where(labels[selected] == 1, 0xEF4444, 0xB8C6D9)
        fields = [PointField(name=name, offset=index*4, datatype=PointField.FLOAT32 if index < 3 else PointField.UINT32, count=1)
                  for index, name in enumerate(("x", "y", "z", "rgb"))]
        message = point_cloud2.create_cloud(Header(frame_id="map"), fields, structured)
        pub = node.create_publisher(type(message), f"/review/{method}/map", qos)
        pubs.append(pub)
        messages.append(message)
        config = {"Panels": [], "Visualization Manager": {"Class": "", "Displays": [
            {"Class": "rviz_default_plugins/Grid", "Name": "World grid", "Enabled": True, "Cell Size": 1,
             "Plane Cell Count": 30, "Color": "65; 70; 85"},
            {"Class": "rviz_default_plugins/PointCloud2", "Name": "Native retained points; red = residual moving-box returns",
             "Enabled": True, "Topic": {"Value": f"/review/{method}/map", "Reliability Policy": "Reliable",
                                        "Durability Policy": "Transient Local", "Depth": 1},
             "Style": "Points", "Size (Pixels)": 1, "Color Transformer": "RGB8", "Position Transformer": "XYZ"},
        ], "Global Options": {"Background Color": "18; 22; 28", "Fixed Frame": "map", "Frame Rate": 15},
            "Tools": [], "Views": {"Current": {"Class": "rviz_default_plugins/Orbit", "Name": "3D result review",
                "Target Frame": "map", "Distance": 12, "Pitch": .72, "Yaw": .8,
                "Focal Point": {"X": 6.4, "Y": 4.5, "Z": .6}}}},
            "Window Geometry": {"Width": 640, "Height": 720, "Hide Left Dock": True, "Hide Right Dock": True}}
        (args.run / f"view-{method}.rviz").write_text(yaml.safe_dump(config, sort_keys=False))
    (args.run / "ready.json").write_text(json.dumps({"scope": "measured native map RESULT REVIEW; no new mapping or localization inference",
                                                       "display_stride": 6, "scores_use": "all confident labelled points",
                                                       "audit_sha256": hashlib.sha256((args.audit / "record.json").read_bytes()).hexdigest(),
                                                       "metrics": metrics}))
    serial = 0
    try:
        while not (args.run / "STOP").exists():
            for pub, message in zip(pubs, messages):
                message.header.stamp = node.get_clock().now().to_msg()
                pub.publish(message)
            serial += 1
            print(f"3D MAP RESULT REVIEW {serial}: red=remaining moving-box points; grey=static. "
                  "Provided mapping-A poses; native DUFOMap / BeautyMap outputs; no new inference.", flush=True)
            rclpy.spin_once(node, timeout_sec=.1)
            time.sleep(.3)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
