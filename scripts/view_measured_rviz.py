"""Publish prepared measured maps to RViz; run with ROS2's system Python."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from std_msgs.msg import Header
from visualization_msgs.msg import Marker
from PyQt5 import QtCore, QtGui, QtWidgets


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--seconds-per-step", type=float, default=7)
    parser.add_argument("--cycles", type=int, default=1, help="0 keeps the inspection open")
    args = parser.parse_args()
    if args.seconds_per_step <= 0 or args.cycles < 0:
        parser.error("Positive step duration and nonnegative cycles required")
    manifest = json.loads(args.manifest.read_text())
    app = QtWidgets.QApplication([])
    panel = QtWidgets.QWidget()
    panel.setWindowTitle("Measured output evidence")
    panel.setGeometry(0, 0, 280, 800)
    panel.setStyleSheet("background:#111b2b;color:#e4edf4;font:15px 'DejaVu Sans';")
    layout = QtWidgets.QVBoxLayout(panel)
    title = QtWidgets.QLabel(manifest["method"].upper())
    title.setStyleSheet("font-size:25px;font-weight:bold;color:#54d9ca;")
    layout.addWidget(title)
    scope = QtWidgets.QLabel("ACTUAL RViz WINDOW\n\nSaved measured output\nNo new mapper inference\nPlayback is not FPS")
    scope.setWordWrap(True)
    layout.addWidget(scope)
    stage = QtWidgets.QLabel()
    stage.setWordWrap(True)
    stage.setStyleSheet("font-size:18px;color:#ffd18a;")
    layout.addWidget(stage)
    detail = QtWidgets.QLabel()
    detail.setWordWrap(True)
    layout.addWidget(detail)
    image_label = QtWidgets.QLabel()
    image_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(image_label)
    semantic = manifest["method"] in ("conceptgraphs", "hovsg")
    legend = ("Native observation above.\n\nOrange: query candidate, not ground truth.\n\n"
              "Saved snapshots where labeled. Final map for query stages." if semantic else
              "Green: removed dynamic\nRed: removed static\nBlue: retained dynamic\nGray: static support\n\n"
              "GT colors for evaluation only, excluded from mapper input.")
    source_label = QtWidgets.QLabel(legend+"\n\nMetric grid; display thinning only.")
    source_label.setWordWrap(True)
    layout.addWidget(source_label)
    layout.addStretch()
    panel.show()
    app.processEvents()
    prepared = []
    for step in manifest["steps"]:
        p = args.manifest.parent / step["file"]
        if sha(p) != step["sha256"]:
            raise ValueError(f"Prepared cloud changed: {p}")
        with np.load(p) as saved:
            prepared.append({k: saved[k] for k in saved.files})
    rclpy.init()
    node = Node("measured_map_review")
    cloud_pub = node.create_publisher(PointCloud2, "/study/cloud", 1)
    image_pub = node.create_publisher(Image, "/study/image", 1)
    marker_pub = node.create_publisher(Marker, "/study/label", 1)
    ready = time.monotonic()
    while cloud_pub.get_subscription_count() == 0 and time.monotonic()-ready < 30:
        rclpy.spin_once(node, timeout_sec=.1)
    started = time.monotonic()
    previous = None
    try:
        while rclpy.ok():
            elapsed = time.monotonic()-started
            serial = int(elapsed/args.seconds_per_step)
            if args.cycles and serial >= len(prepared)*args.cycles:
                break
            idx = serial % len(prepared)
            data, step = prepared[idx], manifest["steps"][idx]
            header = Header(frame_id="map", stamp=node.get_clock().now().to_msg())
            xyz, rgb = data["xyz"], data["rgb"].astype(np.uint32)
            points = np.empty(len(xyz), dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("rgb", "<u4")])
            for axis, col in zip("xyz", xyz.T):
                points[axis] = col
            points["rgb"] = (rgb[:, 0] << 16) | (rgb[:, 1] << 8) | rgb[:, 2]
            fields = [PointField(name=a, offset=i*4, datatype=PointField.FLOAT32, count=1)
                      for i, a in enumerate(("x", "y", "z", "rgb"))]
            cloud_pub.publish(PointCloud2(header=header, height=1, width=len(xyz), fields=fields,
                                         is_bigendian=False, point_step=16, row_step=16*len(xyz),
                                         data=points.tobytes(), is_dense=True))
            if "image" in data:
                im = np.ascontiguousarray(data["image"])
                image_pub.publish(Image(header=header, height=im.shape[0], width=im.shape[1],
                                        encoding="rgb8", step=im.shape[1]*3, data=im.tobytes()))
            marker = Marker(header=header, ns="review", id=0, type=Marker.TEXT_VIEW_FACING,
                            action=Marker.ADD, text=manifest["method"]+"\n"+step["label"].replace(" | ", "\n"))
            marker.pose.position.x, marker.pose.position.y, marker.pose.position.z = manifest["focal_point"]
            marker.pose.position.z += 2
            marker.pose.orientation.w = 1.
            marker.scale.z = .22 if manifest["method"] in ("conceptgraphs", "hovsg") else 1.
            marker.color.r = marker.color.g = marker.color.b = marker.color.a = 1.
            marker_pub.publish(marker)
            if previous != idx:
                stage.setText(step["label"].replace(" | ", "\n\n"))
                detail.setText(f"Step {idx+1}/{len(prepared)}\nDisplayed points: {len(xyz):,}\nSource observation: {step['source_index']}\nData SHA256: {step['sha256'][:16]}")
                if "image" in data:
                    im = np.ascontiguousarray(data["image"])
                    qim = QtGui.QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QtGui.QImage.Format_RGB888)
                    image_label.setPixmap(QtGui.QPixmap.fromImage(qim).scaledToWidth(250))
                print(json.dumps({"elapsed_s": round(elapsed, 3), "step": idx,
                                  "label": step["label"], "points": len(xyz)}), flush=True)
                previous = idx
            app.processEvents()
            rclpy.spin_once(node, timeout_sec=.15)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
