"""Actual Gazebo 3D inputs + provided poses; periodic native cleaning, never online BeautyMap."""

import json
import os
import sys
from collections import deque
from pathlib import Path

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tf2_ros import Buffer, TransformListener
from rclpy.executors import ExternalShutdownException
from visualization_msgs.msg import Marker

from observe_session import matrix, seconds


def atomic_json(path, payload):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(path)


def configure(run, methods, dimension):
    runtime = json.loads((run / "runtime.json").read_text())
    x, y = (7.5, -3.1) if runtime["scene"] == "corridor" else (7.5, 3.0)
    for index, method in enumerate(methods):
        display = (
            f"""    - Class: rviz_default_plugins/PointCloud2
      Name: {method} - measured 3D points
      Enabled: true
      Topic:
        Value: /compare/{method}/points
        Durability Policy: Transient Local
      Style: Points
      Size (Pixels): 2
      Color Transformer: AxisColor
      Axis: Z
      Position Transformer: XYZ
"""
            if dimension == "3d"
            else f"""    - Class: rviz_default_plugins/Map
      Name: {method} - 3D map projected to 2D (NOT native 2D algorithm)
      Enabled: true
      Topic:
        Value: /compare/{method}/map
        Durability Policy: Transient Local
      Alpha: 1
      Color Scheme: map
"""
        )
        view = (
            f"""      Class: rviz_default_plugins/Orbit
      Distance: 19
      Pitch: 0.8
      Yaw: 0.7
      Focal Point:
        X: {x}
        Y: {y}
        Z: 0
"""
            if dimension == "3d"
            else f"""      Class: rviz_default_plugins/TopDownOrtho
      Scale: 30
      Angle: 0
      X: {x}
      Y: {y}
"""
        )
        text = f"""Panels: []
Visualization Manager:
  Displays:
{display}    - Class: rviz_default_plugins/Marker
      Name: Input cutoff and processing scope
      Enabled: true
      Topic:
        Value: /compare/{method}/status
  Global Options:
    Background Color: 18; 22; 28
    Fixed Frame: world
    Frame Rate: 10
  Views:
    Current:
{view}      Target Frame: world
Window Geometry:
  Height: 650
  Width: 640
  X: {index * 640}
  Y: 0
  Hide Left Dock: true
  Hide Right Dock: true
"""
        (run / f"compare-{method}.rviz").write_text(text)
    atomic_json(run / "compare-configs.json", {"methods": methods, "dimension": dimension})


class LiveComparison:
    def __init__(self, run, truth_path):
        self.run = run
        self.methods = os.environ.get("PRESENTATION_COMPARE_METHODS", "raw,dufomap,beautymap").split(",")
        self.dimension = "3d" if "-3d-" in os.environ["PRESENTATION_FLOW"] else "2d"
        configure(run, self.methods, self.dimension)
        self.node = rclpy.create_node("provided_pose_mapping_comparison")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self.node)
        self.truth_file = truth_path.open()
        self.truth = deque(maxlen=3000)
        self.pending = deque()
        self.scans, self.poses, self.stamps = [], [], []
        self.last_scan = -10
        self.last_snapshot = -30
        self.version = 0
        self.last_result = None
        self.rejected = 0
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.cloud_pub = {
            m: self.node.create_publisher(PointCloud2, f"/compare/{m}/points", qos) for m in self.methods
        }
        self.map_pub = {
            m: self.node.create_publisher(OccupancyGrid, f"/compare/{m}/map", qos) for m in self.methods
        }
        self.status_pub = {
            m: self.node.create_publisher(Marker, f"/compare/{m}/status", 1) for m in self.methods
        }
        self.node.create_subscription(PointCloud2, "/points", self.on_cloud, qos_profile_sensor_data)
        self.node.create_timer(0.3, self.tick)
        self.cutoff = None

    def on_cloud(self, msg):
        if seconds(msg.header.stamp) - self.last_scan >= 1:
            self.pending.append(msg)
            self.last_scan = seconds(msg.header.stamp)

    def read_truth(self):
        while True:
            start = self.truth_file.tell()
            line = self.truth_file.readline()
            if not line or not line.endswith("\n"):
                self.truth_file.seek(start)
                break
            self.truth.append(json.loads(line))

    def publish_map(self, method, folder):
        settings = (folder / "map.yaml").read_text()
        import re

        resolution = float(re.search(r"resolution: ([\d.]+)", settings).group(1))
        origin = [float(x) for x in re.search(r"origin: \[([^]]+)\]", settings).group(1).split(",")]
        data = (folder / "map.pgm").read_bytes()
        match = re.match(rb"P5\s+(\d+)\s+(\d+)\s+255\s", data)
        width, height = map(int, match.groups())
        pixels = np.flipud(np.frombuffer(data[match.end() :], dtype=np.uint8).reshape(height, width))
        grid = OccupancyGrid()
        grid.header = Header(frame_id="world", stamp=self.node.get_clock().now().to_msg())
        grid.info.resolution, grid.info.width, grid.info.height = resolution, width, height
        grid.info.origin.position.x, grid.info.origin.position.y = origin[:2]
        grid.info.origin.orientation.w = 1.0
        grid.data = (
            np.where(pixels == 0, 100, np.where(pixels == 254, 0, -1)).astype(np.int8).ravel().tolist()
        )
        self.map_pub[method].publish(grid)

    def tick(self):
        self.read_truth()
        for _ in range(len(self.pending)):
            msg = self.pending.popleft()
            stamp = seconds(msg.header.stamp)
            if not self.truth or stamp > self.truth[-1]["stamp_s"]:
                self.pending.append(msg)
                continue
            truth = min(self.truth, key=lambda t: abs(t["stamp_s"] - stamp))
            if abs(truth["stamp_s"] - stamp) > 0.05:
                self.rejected += 1
                continue
            try:
                t = self.tf.lookup_transform(
                    "base_footprint", msg.header.frame_id, rclpy.time.Time()
                ).transform
            except Exception:
                self.pending.append(msg)
                continue
            p, q = t.translation, t.rotation
            pose = matrix(truth["xyz"], truth["xyzw"]) @ matrix([p.x, p.y, p.z], [q.x, q.y, q.z, q.w])
            points = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True)
            points = points[np.isfinite(points).all(axis=1) & (np.linalg.norm(points, axis=1) > 0.30)]
            self.scans.append(points.astype(np.float32))
            self.poses.append(pose)
            self.stamps.append(stamp)
        if len(self.scans) >= 5 and self.stamps[-1] - self.last_snapshot >= 15:
            # Immutable inputs avoid races with the slower, isolated author runtime.
            self.version += 1
            folder = self.run / f"compare-input-{self.version:04d}"
            folder.mkdir()
            ids = np.linspace(0, len(self.scans) - 1, min(60, len(self.scans)), dtype=int)
            archive = {f"scan_{i:04d}": self.scans[j] for i, j in enumerate(ids)}
            archive["poses"] = np.asarray(self.poses)[ids]
            archive["stamps"] = np.asarray(self.stamps)[ids]
            np.savez_compressed(folder / "mapping-clouds.npz", **archive)
            (folder / "runtime.json").write_bytes((self.run / "runtime.json").read_bytes())
            self.last_snapshot = self.stamps[-1]
            atomic_json(
                self.run / "compare-input.json",
                {
                    "version": self.version,
                    "path": str(folder),
                    "last_input_sim_s": self.last_snapshot,
                    "scans": len(ids),
                    "source": "actual Gazebo 16-line clouds; provided synchronized truth poses",
                    "native_2d": False,
                    "processing": "periodic independent batch; BeautyMap is offline",
                },
            )
        marker = self.run / "compare-result.json"
        if marker.exists():
            result = json.loads(marker.read_text())
            if result["version"] != self.last_result:
                for method in self.methods:
                    folder = Path(result["output"]) / method
                    if self.dimension == "2d":
                        self.publish_map(method, folder)
                    else:
                        points = np.load(folder / "points.npy")
                        header = Header(frame_id="world", stamp=self.node.get_clock().now().to_msg())
                        self.cloud_pub[method].publish(point_cloud2.create_cloud_xyz32(header, points))
                self.cutoff = result["last_input_sim_s"]
                self.last_result = result["version"]
                atomic_json(self.run / "compare-displayed.json", result)
        for method in self.methods:
            label = Marker()
            label.header = Header(frame_id="world", stamp=self.node.get_clock().now().to_msg())
            label.type, label.action = Marker.TEXT_VIEW_FACING, Marker.ADD
            label.pose.position.x = 7.5
            if self.dimension == "3d":
                label.pose.position.y = -3.1 if "corridor" in os.environ["PRESENTATION_FLOW"] else 3.0
            else:
                label.pose.position.y = -0.5 if "corridor" in os.environ["PRESENTATION_FLOW"] else 10.0
            label.pose.position.z, label.pose.orientation.w = 3.5, 1.0
            label.scale.z = 0.35
            label.color.r, label.color.g, label.color.b, label.color.a = 1.0, 1.0, 1.0, 1.0
            cutoff = (
                "WAITING for first batch"
                if self.cutoff is None
                else f"same-input cutoff: {self.cutoff:.1f} sim s"
            )
            label.text = f"{method} | {self.dimension.upper()}\n{cutoff}\nProvided mapping poses\nPeriodic batch (offline)"
            self.status_pub[method].publish(label)


if __name__ == "__main__":
    rclpy.init()
    comparison = LiveComparison(Path(sys.argv[1]), Path(sys.argv[2]))
    try:
        rclpy.spin(comparison.node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        comparison.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
