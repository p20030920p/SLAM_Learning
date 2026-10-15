"""Live ROS adapter for project-written 2D mapping experiments; no truth input."""

import json
import math
from collections import deque
from pathlib import Path
import sys

import numpy as np
import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tf2_ros import Buffer, TransformListener

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from slam_learning.runtime.own_mapping import RayEvidence, deskew, interpolate_pose, pose2, transform


def stamp(msg):
    return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


class Live:
    def __init__(self, run):
        self.run = run
        self.runtime = json.loads((run / "runtime.json").read_text())
        self.motion = "motion" in self.runtime["flow"]
        self.methods = ("off", "deskew") if self.motion else (("strict", "protected") if self.runtime["scene"] == "corridor" else ("raw", "temporal"))
        self.node = rclpy.create_node("project_own_mapping")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self.node)
        self.anchor = pose2(*self.runtime["spawn"])
        self.odometry, self.pending = deque(maxlen=5000), deque()
        self.evidence = {name: RayEvidence() for name in self.methods}
        self.parts, self.scans, self.archive = [], [], {}
        self.last = self.last_publish = -1e9
        self.start = None
        self.cmd = self.node.create_publisher(Twist, "/cmd_vel", 10)
        self.clouds = {name: self.node.create_publisher(PointCloud2, f"/own/{name}", 1) for name in self.methods}
        self.map_pub = self.node.create_publisher(OccupancyGrid, "/map", QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.node.create_subscription(Odometry, "/omni_drive_controller/odom", self.odom, qos_profile_sensor_data)
        self.node.create_subscription(LaserScan, "/scan", self.scan, qos_profile_sensor_data)
        self.node.create_timer(.03, self.tick)

    def odom(self, msg):
        p = msg.pose.pose
        self.odometry.append((stamp(msg), [p.position.x, p.position.y, yaw(p.orientation)]))

    def scan(self, msg):
        if stamp(msg) - self.last >= (.099 if self.motion else .199):
            self.pending.append(msg)
            self.last = stamp(msg)

    def tick(self):
        now = self.node.get_clock().now().nanoseconds * 1e-9
        if (self.run / "recording.started").exists() and self.start is None:
            self.start = now
        if self.motion and self.start is not None:
            elapsed = now - self.start
            cmd = Twist()
            if 7 <= elapsed < 15:
                cmd.angular.z = .12
            elif 15 <= elapsed < 23:
                cmd.angular.z = .8
            elif 23 <= elapsed < 31:
                cmd.angular.z = -.8
            elif 31 <= elapsed < 35:
                cmd.linear.x = .25
            elif 35 <= elapsed < 39:
                cmd.linear.x = -.25
            self.cmd.publish(cmd)
        while self.pending and len(self.odometry) >= 2:
            msg = self.pending[0]
            t = stamp(msg)
            if t > self.odometry[-1][0]:
                break
            self.pending.popleft()
            if t < self.odometry[0][0]:
                continue
            try:
                tf = self.tf.lookup_transform("base_footprint", msg.header.frame_id, rclpy.time.Time()).transform
            except Exception:
                continue
            extrinsic = pose2(tf.translation.x, tf.translation.y, yaw(tf.rotation))
            times = np.array([item[0] for item in self.odometry])
            poses = np.array([item[1] for item in self.odometry])
            sensor_pose = self.anchor @ interpolate_pose(times, poses, t) @ extrinsic
            ranges = np.asarray(msg.ranges)
            angles = msg.angle_min + np.arange(len(ranges)) * msg.angle_increment
            valid = np.isfinite(ranges) & (ranges > .45) & (ranges < 12.)
            if self.runtime["scene"] == "corridor":
                # Same deliberately sparse, short-range input in both controls.
                valid &= (ranges < 3.5) & (np.abs(angles) < 2 * np.pi / 3)
                valid &= np.arange(len(ranges)) % 10 == 0
            indices = np.arange(len(ranges))[valid]
            points = np.column_stack((ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid])))
            key = f"scan_{len(self.scans):05d}"
            self.archive[key] = points.astype(np.float32)
            self.scans.append({"key": key, "stamp_s": t, "sensor_pose": sensor_pose.tolist(), "extrinsic": extrinsic.tolist(), "sensor_z": tf.translation.z})
            if self.motion:
                sector = len(self.parts)
                chosen = (indices * 3 // len(ranges)).clip(0, 2) == sector
                self.parts.append((t, points[chosen], sensor_pose))
                if len(self.parts) < 3:
                    continue
                values = np.concatenate([item[1] for item in self.parts])
                point_times = np.concatenate([np.full(len(item[1]), item[0]) for item in self.parts])
                # Wheel odometry includes the measured sensor offset at every time.
                laser_poses = [self.anchor @ pose2(*p) @ extrinsic for p in poses]
                laser_vectors = np.array([[p[0, 2], p[1, 2], np.arctan2(p[1, 0], p[0, 0])] for p in laser_poses])
                corrected = deskew(values, point_times, times, laser_vectors, t)
                for name, local in [("off", values), ("deskew", corrected)]:
                    self.evidence[name].add(transform(local, sensor_pose), sensor_pose[:2, 2], t)
                self.parts = []
            else:
                world = transform(points, sensor_pose)
                for evidence in self.evidence.values():
                    evidence.add(world, sensor_pose[:2, 2], t)
            if t - self.last_publish >= 1.:
                self.publish(t)

    def publish(self, t):
        self.last_publish = t
        header = Header(frame_id="map", stamp=self.node.get_clock().now().to_msg())
        for name, evidence in self.evidence.items():
            points = evidence.points(name)
            xyz = np.column_stack((points, np.zeros(len(points))))
            self.clouds[name].publish(point_cloud2.create_cloud_xyz32(header, xyz.astype(np.float32)))
        evidence = self.evidence[self.methods[-1]]
        image = evidence.image(self.methods[-1])
        grid = OccupancyGrid(header=header)
        grid.info.resolution = evidence.resolution
        grid.info.width, grid.info.height = image.shape[1], image.shape[0]
        grid.info.origin.position.x, grid.info.origin.position.y = map(float, evidence.origin)
        grid.info.origin.orientation.w = 1.
        grid.data = np.where(image == 0, 100, np.where(image == 254, 0, -1)).astype(np.int8).ravel().tolist()
        self.map_pub.publish(grid)
        print(f"Own mapping scans={len(self.scans)} {[(n, len(e.points(n))) for n, e in self.evidence.items()]}", flush=True)

    def close(self):
        self.cmd.publish(Twist())
        for name, evidence in self.evidence.items():
            evidence.save(self.run / "maps" / name, name)
        np.savez_compressed(self.run / "own-inputs.npz", **self.archive)
        (self.run / "own-scans.json").write_text(json.dumps(self.scans))
        (self.run / "own-odom.json").write_text(json.dumps(list(self.odometry)))
        (self.run / "own-finished.json").write_text(json.dumps({"methods": self.methods, "scans": len(self.scans), "truth_used": False, "mapping_pose": "interpolated wheel odometry and fixed configured start"}))


if __name__ == "__main__":
    rclpy.init()
    live = Live(Path(sys.argv[1]))
    try:
        while rclpy.ok() and not (live.run / "finished.json").exists() and not (live.run / "STOP").exists():
            rclpy.spin_once(live.node, timeout_sec=.03)
    finally:
        live.close()
        live.node.destroy_node()
        rclpy.shutdown()
