"""Form sequential sector scans from real Gazebo samples, log native outputs.

No truth is read or used to manufacture motion distortion. Each scan is three
successive angular sectors; all points in a sector retain its actual timestamp.
"""

import json
import math
from pathlib import Path
import sys

import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2, PointField, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header


class Transport:
    def __init__(self, run):
        self.run = run
        self.node = rclpy.create_node("rolling_sector_transport")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.pub = self.node.create_publisher(PointCloud2, "/study/rolling", 10)
        self.imu_pub = self.node.create_publisher(Imu, "/study/imu_ready", 1000)
        self.cmd = self.node.create_publisher(Twist, "/cmd_vel", 10)
        self.parts = []
        self.imu_count = 0
        self.count = 0
        self.start = None
        self.log = (run / "rolling-scans.jsonl").open("w")
        self.imu_log = (run / "imu.jsonl").open("w")
        self.outputs = {n: (run / f"fastlio-{n}.jsonl").open("w") for n in ("deskew", "no_deskew")}
        self.cloud_logs = {n: (run / f"fastlio-{n}-clouds.npz") for n in self.outputs}
        self.clouds = {n: {} for n in self.outputs}
        self.node.create_subscription(PointCloud2, "/points", self.cloud, qos_profile_sensor_data)
        self.node.create_subscription(Imu, "/study/imu", self.imu, qos_profile_sensor_data)
        for name in self.outputs:
            self.node.create_subscription(
                Odometry, f"/{name}/Odometry", lambda m, n=name: self.odom(m, n), 10
            )
            self.node.create_subscription(
                PointCloud2, f"/{name}/cloud_registered", lambda m, n=name: self.output_cloud(m, n), 10
            )
        self.node.create_timer(0.05, self.control)

    def stamp(self, msg):
        return msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9

    def imu(self, msg):
        if self.stamp(msg) >= 3.0:
            self.imu_pub.publish(msg)
        self.imu_count += 1
        self.imu_log.write(
            json.dumps(
                {
                    "t": self.stamp(msg),
                    "a": [msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z],
                    "w": [msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z],
                }
            )
            + "\n"
        )

    def odom(self, msg, name):
        p = msg.pose.pose
        row = {
            "t": self.stamp(msg),
            "p": [p.position.x, p.position.y, p.position.z],
            "q": [p.orientation.x, p.orientation.y, p.orientation.z, p.orientation.w],
        }
        self.outputs[name].write(json.dumps(row) + "\n")
        self.outputs[name].flush()

    def output_cloud(self, msg, name):
        # Save every native registered cloud; paired scoring chooses exact stamps.
        t = self.stamp(msg)
        key = f"t_{t:.6f}"
        a = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True)
        self.clouds[name][key] = np.asarray(a, dtype=np.float32)[::3]

    def cloud(self, msg):
        if self.stamp(msg) < 3.0:
            return
        a = np.asarray(point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True))
        a = a[np.isfinite(a).all(axis=1)]
        if not len(a):
            return
        stamp = self.stamp(msg)
        part = len(self.parts)
        angle = np.arctan2(a[:, 1], a[:, 0])
        sector = np.floor((angle + math.pi) / (2 * math.pi) * 3).astype(int).clip(0, 2)
        a = a[(sector == part) & (np.linalg.norm(a, axis=1) > 0.4)]
        elev = np.arctan2(a[:, 2], np.linalg.norm(a[:, :2], axis=1))
        ring = np.rint((elev + math.pi / 12) / (math.pi / 6) * 15).clip(0, 15).astype(np.uint16)
        self.parts.append((stamp, a, ring))
        if len(self.parts) < 3:
            return
        t0 = self.parts[0][0]
        fields = [
            PointField(name=n, offset=o, datatype=d, count=1)
            for n, o, d in [
                ("x", 0, 7),
                ("y", 4, 7),
                ("z", 8, 7),
                ("intensity", 12, 7),
                ("ring", 16, 4),
                ("time", 20, 7),
            ]
        ]
        dtype = np.dtype(
            {
                "names": ["x", "y", "z", "intensity", "ring", "time"],
                "formats": ["<f4", "<f4", "<f4", "<f4", "<u2", "<f4"],
                "offsets": [0, 4, 8, 12, 16, 20],
                "itemsize": 24,
            }
        )
        result = np.zeros(sum(len(p[1]) for p in self.parts), dtype=dtype)
        cursor = 0
        for t, points, rings in self.parts:
            dest = result[cursor : cursor + len(points)]
            for i, name in enumerate(("x", "y", "z")):
                dest[name] = points[:, i]
            dest["intensity"] = 1
            dest["ring"] = rings
            dest["time"] = t - t0
            cursor += len(points)
        header = Header(frame_id="lidar_3d_link")
        header.stamp.sec = int(t0)
        header.stamp.nanosec = round((t0 - int(t0)) * 1e9)
        self.pub.publish(point_cloud2.create_cloud(header, fields, result))
        self.count += 1
        self.log.write(
            json.dumps(
                {
                    "begin": t0,
                    "end": stamp,
                    "points": len(result),
                    "packet_times": [p[0] for p in self.parts],
                    "imu_count": self.imu_count,
                }
            )
            + "\n"
        )
        self.log.flush()
        self.parts = []
        if self.count % 10 == 0:
            print(
                f"Native rolling scans={self.count} IMU={self.imu_count} span={stamp - t0:.3f}s", flush=True
            )

    def control(self):
        if not (self.run / "recording.started").exists():
            return
        now = self.node.get_clock().now().nanoseconds * 1e-9
        if self.start is None:
            self.start = now
        t = now - self.start
        cmd = Twist()
        if 7 <= t < 15:
            cmd.angular.z = 0.12
        elif 15 <= t < 23:
            cmd.angular.z = 0.8
        elif 23 <= t < 31:
            cmd.angular.z = -0.8
        elif 31 <= t < 35:
            cmd.linear.x = 0.25
        elif 35 <= t < 39:
            cmd.linear.x = -0.25
        self.cmd.publish(cmd)

    def close(self):
        self.cmd.publish(Twist())
        self.log.close()
        self.imu_log.close()
        for n, f in self.outputs.items():
            f.close()
            np.savez_compressed(self.cloud_logs[n], **self.clouds[n])
        (self.run / "fastlio-transport-finished.json").write_text(
            json.dumps({"rolling_scans": self.count, "imu_samples": self.imu_count})
        )


if __name__ == "__main__":
    rclpy.init()
    obj = Transport(Path(sys.argv[1]))
    try:
        while rclpy.ok() and not (obj.run / "finished.json").exists():
            rclpy.spin_once(obj.node, timeout_sec=0.05)
    finally:
        obj.close()
