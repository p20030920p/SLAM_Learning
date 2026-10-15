"""Live sensor-only B: matched hypothesis ablations; simulator truth is unavailable here."""
import copy
import hashlib
import json
import math
import sys
import time
from collections import deque
from pathlib import Path

import numpy as np
import rclpy
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Odometry, Path as RosPath
from PIL import Image
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tf2_ros import Buffer, TransformListener

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from slam_learning.runtime.recovery_probe import Probe, SurfaceMap, compose, inverse, transform, voxel
from observe_session import matrix, seconds, yaw


class Localizer:
    def __init__(self, run):
        self.node = rclpy.create_node("hypothesis_sensor_only_localizer")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.sensor_callbacks = ReentrantCallbackGroup()
        self.compute_callbacks = MutuallyExclusiveCallbackGroup()
        self.run = run
        self.config = json.loads((run / "probe-config.json").read_text())
        self.cases = json.loads((run / "cases.json").read_text())
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self.node)
        self.odom = deque(maxlen=5000)
        self.depth = deque(maxlen=30)
        self.pending = deque(maxlen=5)
        self.last_queued = -1e9
        self.last = -1e9
        self.frame = 0
        self.log = (run / "probe-updates.jsonl").open("w")
        self.inputs = {}
        self.input_rows = []
        initial = self.cases["plain"]["initial_pose"]
        self.probes = {name: Probe([initial["x"], initial["y"], initial["yaw"]], **options)
                       for name, options in self.config["variants"].items()}
        self.lidar_map = SurfaceMap(np.load(self.config["lidar_map"], allow_pickle=False), 2 if self.config["dimension"] == "2d" else 3)
        self.depth_map = SurfaceMap(np.load(self.config["depth_map"], allow_pickle=False), 3)
        self.paths, self.pose_pubs, self.path_pubs = {}, {}, {}
        for name in self.cases:
            self.paths[name] = RosPath(header=Header(frame_id="map"))
            self.path_pubs[name] = self.node.create_publisher(RosPath, f"/{name}/probe_path", 3)
            if name != "native":
                self.pose_pubs[name] = self.node.create_publisher(PoseWithCovarianceStamped, self.cases[name]["pose_topic"], 20)
        self.node.create_subscription(PoseWithCovarianceStamped, self.cases["native"]["pose_topic"], lambda msg: self.path("native", msg), 30)
        self.node.create_subscription(Odometry, "/omni_drive_controller/odom", lambda msg: self.odom.append(msg), 100, callback_group=self.sensor_callbacks)
        self.node.create_subscription(PointCloud2, "/depth/points", lambda msg: self.depth.append(msg), qos_profile_sensor_data, callback_group=self.sensor_callbacks)
        if self.config["dimension"] == "2d":
            self.node.create_subscription(LaserScan, self.config["scan_topic"], self.receive, qos_profile_sensor_data, callback_group=self.sensor_callbacks)
        else:
            self.node.create_subscription(PointCloud2, self.config["cloud_topic"], self.receive, qos_profile_sensor_data, callback_group=self.sensor_callbacks)
        durable = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL, reliability=ReliabilityPolicy.RELIABLE)
        self.map_pub = self.node.create_publisher(OccupancyGrid, "/plain/map", durable)
        self.points_pub = self.node.create_publisher(PointCloud2, "/probe/map_points", durable)
        self.publish_map()
        self.node.create_timer(.03, self.step, callback_group=self.compute_callbacks)
        (run / "probes-ready.json").write_text(json.dumps({"cases": list(self.probes)}))

    def publish_map(self):
        import yaml
        path = Path(self.cases["plain"]["map_yaml"])
        settings = yaml.safe_load(path.read_text())
        pixels = np.flipud(np.asarray(Image.open(path.parent / "map.pgm")))
        msg = OccupancyGrid(header=Header(frame_id="map"))
        msg.info.resolution = settings["resolution"]
        msg.info.height, msg.info.width = pixels.shape
        msg.info.origin.position.x, msg.info.origin.position.y = settings["origin"][:2]
        msg.info.origin.orientation.w = 1.
        msg.data = np.where(pixels == 205, -1, np.where(pixels == 0, 100, 0)).astype(np.int8).ravel().tolist()
        self.map_pub.publish(msg)
        self.points_pub.publish(point_cloud2.create_cloud_xyz32(Header(frame_id="map"), self.lidar_map.points.astype(np.float32)))

    def points(self, msg, depth=False):
        if isinstance(msg, LaserScan):
            ranges = np.asarray(msg.ranges)
            angles = msg.angle_min + np.arange(len(ranges)) * msg.angle_increment
            valid = np.isfinite(ranges) & (ranges > .45) & (ranges < 12.01)
            xyz = np.column_stack((ranges[valid] * np.cos(angles[valid]), ranges[valid] * np.sin(angles[valid]), np.zeros(valid.sum())))
        else:
            xyz = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True).reshape(-1, 3)
            if depth:
                xyz = xyz[::8]
            distance = np.linalg.norm(xyz, axis=1)
            xyz = xyz[np.isfinite(xyz).all(axis=1) & (distance > (.25 if depth else .45)) & (distance < (4.01 if depth else 12.01))]
        extrinsic = self.tf.lookup_transform("base_footprint", msg.header.frame_id, rclpy.time.Time()).transform
        p, q = extrinsic.translation, extrinsic.rotation
        pose = matrix([p.x, p.y, p.z], [q.x, q.y, q.z, q.w])
        xyz = xyz @ pose[:3, :3].T + pose[:3, 3]
        xyz = xyz[(xyz[:, 2] > .12) & (xyz[:, 2] < 2.4)]
        return voxel(xyz, .08, 850)

    def path(self, name, msg):
        path = self.paths[name]
        path.header.stamp = copy.deepcopy(msg.header.stamp)
        path.poses.append(PoseStamped(header=copy.deepcopy(msg.header), pose=copy.deepcopy(msg.pose.pose)))
        self.path_pubs[name].publish(path)

    def receive(self, msg):
        stamp = seconds(msg.header.stamp)
        if stamp - self.last_queued >= .3:
            self.pending.append(msg)
            self.last_queued = stamp

    def step(self):
        if not self.pending or not self.odom:
            return
        msg = self.pending[0]
        stamp = seconds(msg.header.stamp)
        # Sensor callbacks only buffer. Wait for equally timestamped depth/odom
        # before doing CPU-heavy fitting, rather than inspecting stale callbacks.
        latest_depth = seconds(self.depth[-1].header.stamp) if self.depth else -1e9
        latest_odom = seconds(self.odom[-1].header.stamp)
        now = self.node.get_clock().now().nanoseconds * 1e-9
        if (latest_depth < stamp or latest_odom < stamp) and now - stamp < .7:
            return
        self.pending.popleft()
        odom = min(list(self.odom), key=lambda item: abs(seconds(item.header.stamp) - stamp))
        if abs(seconds(odom.header.stamp) - stamp) > .12:
            return
        try:
            lidar = self.points(msg)
            depth_msg = min(list(self.depth), key=lambda item: abs(seconds(item.header.stamp) - stamp)) if self.depth else None
            depth_delta = abs(seconds(depth_msg.header.stamp) - stamp) if depth_msg else None
            depth = self.points(depth_msg, depth=True) if depth_delta is not None and depth_delta <= .12 else np.empty((0, 3))
        except Exception as error:
            self.node.get_logger().warning(str(error))
            return
        if len(lidar) < 12:
            return
        self.last = stamp
        started = time.monotonic()
        p = odom.pose.pose
        wheel = np.array([p.position.x, p.position.y, yaw(p.orientation)])
        depth_odom_delta = None
        if len(depth):
            depth_stamp = seconds(depth_msg.header.stamp)
            depth_odom = min(list(self.odom), key=lambda item: abs(seconds(item.header.stamp) - depth_stamp))
            depth_odom_delta = abs(seconds(depth_odom.header.stamp) - depth_stamp)
            if depth_odom_delta <= .12:
                p_depth = depth_odom.pose.pose
                wheel_depth = np.array([p_depth.position.x, p_depth.position.y, yaw(p_depth.orientation)])
                depth = transform(depth, compose(inverse(wheel), wheel_depth))
            else:
                depth = np.empty((0, 3))
        key = f"frame_{self.frame:05d}"
        self.inputs[key + "_lidar"] = lidar.copy()
        self.inputs[key + "_depth"] = depth.copy()
        self.inputs[key + "_odom"] = wheel
        self.input_rows.append({"frame": self.frame, "stamp_s": stamp, "depth_delta_s": depth_delta,
                                "depth_odom_delta_s": depth_odom_delta, "depth_motion_compensated": bool(len(depth)),
                                "odom_delta_s": abs(seconds(odom.header.stamp) - stamp),
                                "lidar_points": len(lidar), "depth_points": len(depth)})
        input_hash = hashlib.sha256(lidar.tobytes() + depth.tobytes() + wheel.tobytes()).hexdigest()
        for name, probe in self.probes.items():
            pose, info = probe.update(stamp, wheel, (self.lidar_map, lidar), (self.depth_map, depth) if len(depth) >= 12 else None)
            output = PoseWithCovarianceStamped(header=Header(stamp=copy.deepcopy(msg.header.stamp), frame_id="map"))
            output.pose.pose.position.x, output.pose.pose.position.y = map(float, pose[:2])
            output.pose.pose.orientation.z, output.pose.pose.orientation.w = math.sin(pose[2] / 2), math.cos(pose[2] / 2)
            output.pose.covariance[0] = output.pose.covariance[7] = .01 if info["rank"] == 3 else 1.
            output.pose.covariance[35] = .01
            self.pose_pubs[name].publish(output)
            self.path(name, output)
            self.log.write(json.dumps({"frame": self.frame, "stamp_s": stamp, "case": name,
                                       "input_sha256": input_hash, "pose": pose.tolist(), **info}) + "\n")
        self.log.flush()
        if self.frame % 15 == 0:
            print(f"SENSOR PROBES frame={self.frame} t={stamp:.2f} lidar={len(lidar)} depth={len(depth)} update_wall={time.monotonic()-started:.3f}s", flush=True)
        self.frame += 1

    def save(self):
        np.savez_compressed(self.run / "probe-B-inputs.npz", **self.inputs)
        (self.run / "probe-B-inputs.json").write_text(json.dumps({"scope": "post-TF sensor/odom inputs; no truth or world geometry", "frames": self.input_rows}, indent=2) + "\n")
        self.log.close()


def main():
    rclpy.init()
    localizer = Localizer(Path(sys.argv[1]))
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(localizer.node)
    try:
        while rclpy.ok():
            executor.spin_once(timeout_sec=.03)
            if (localizer.run / "finished.json").exists() or (localizer.run / "STOP").exists():
                break
    finally:
        executor.shutdown(timeout_sec=10)
        localizer.save()
        localizer.node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
