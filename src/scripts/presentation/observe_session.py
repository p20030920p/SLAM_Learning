"""Collect live sensor data and independently timestamped simulator truth."""

from __future__ import annotations

import argparse
import csv
import json
import math
import select
import sys
import termios
import time
import tty
from collections import deque
from pathlib import Path

import numpy as np
import rclpy
from geometry_msgs.msg import PoseWithCovarianceStamped, TransformStamped, Twist
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from tf2_ros import Buffer, TransformBroadcaster, TransformListener


def seconds(stamp):
    return stamp.sec + stamp.nanosec * 1e-9


def matrix(xyz, xyzw):
    x, y, z, w = np.asarray(xyzw) / np.linalg.norm(xyzw)
    result = np.eye(4)
    result[:3, :3] = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    result[:3, 3] = xyz
    return result


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


class Observer:
    def __init__(self, args):
        self.args = args
        self.run = args.run
        session_flow = json.loads((self.run / "session.json").read_text())["flow"]
        self.simple_probe = "-probe-" in session_flow and "-2d-" in session_flow
        self.node = rclpy.create_node("presentation_observer")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self.node)
        self.broadcaster = TransformBroadcaster(self.node)
        self.truth = deque(maxlen=30000)
        self.truth_stream = args.truth.open()
        self.failure = None
        self.pending = deque()
        self.clouds, self.poses, self.cloud_stamps = [], [], []
        self.last_cloud = -math.inf
        self.odom, self.map_transform = None, None
        self.points_received = 0
        self.scans_received = 0
        self.map_info = None
        self.started_sim = None
        self.started_wall = time.monotonic()
        self.start_record_wall = None
        self.last_print = 0
        self.last_control = 0
        self.keys = Twist()
        self.case_names = args.cases.split(",") if args.cases else []
        self.cases = json.loads((self.run / "cases.json").read_text())
        self.rows = {case: [] for case in self.case_names}
        self.seen_poses = {case: set() for case in self.case_names}
        self.files = {}
        self.writers = {}
        self.pose3d_files, self.pose3d_writers = {}, {}
        self.dropped = {case: 0 for case in self.case_names}
        self.command_pub = self.node.create_publisher(Twist, "/cmd_vel", 10)
        self.node.create_subscription(Odometry, "/omni_drive_controller/odom", self.on_odom, 20)
        self.node.create_subscription(PointCloud2, "/points", self.on_cloud, qos_profile_sensor_data)
        self.node.create_subscription(LaserScan, "/scan", self.on_scan_receipt, qos_profile_sensor_data)
        map_topic = "/map" if args.mode == "mapping" else f"/{self.case_names[0]}/map"
        for durable in (DurabilityPolicy.TRANSIENT_LOCAL, DurabilityPolicy.VOLATILE):
            qos = QoSProfile(depth=1, durability=durable, reliability=ReliabilityPolicy.RELIABLE)
            self.node.create_subscription(OccupancyGrid, map_topic, self.on_map, qos)
        for case in self.case_names:
            if self.cases[case].get("dimension") == "3d":
                self.pose3d_files[case] = (self.run / f"{case}-poses3d.csv").open("w", newline="")
                self.pose3d_writers[case] = csv.writer(self.pose3d_files[case])
                self.pose3d_writers[case].writerow(["stamp_s", *["truth_"+key for key in ("x", "y", "z", "qx", "qy", "qz", "qw")],
                                                   *["estimate_"+key for key in ("x", "y", "z", "qx", "qy", "qz", "qw")], "nearest_truth_delta_s"])
            self.files[case] = (self.run / f"{case}-samples.csv").open("w", newline="")
            self.writers[case] = csv.writer(self.files[case])
            self.writers[case].writerow(
                [
                    "stamp_s",
                    "truth_x",
                    "truth_y",
                    "truth_yaw",
                    "estimate_x",
                    "estimate_y",
                    "estimate_yaw",
                    "position_error_m",
                    "yaw_error_rad",
                    "nearest_truth_delta_s",
                ]
            )
            self.node.create_subscription(
                PoseWithCovarianceStamped,
                self.cases[case].get("pose_topic", f"/{case}/amcl_pose"),
                lambda msg, name=case: self.pending.append(("pose", name, msg)),
                20,
            )
            if self.cases[case].get("localizer", "AMCL") == "AMCL":
                # AMCL's retained initial pose can precede observer discovery.
                # A stationary robot must not deadlock recording readiness.
                retained = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                                      reliability=ReliabilityPolicy.RELIABLE)
                self.node.create_subscription(
                    PoseWithCovarianceStamped,
                    self.cases[case].get("pose_topic", f"/{case}/amcl_pose"),
                    lambda msg, name=case: self.pending.append(("pose", name, msg)), retained)

    def on_odom(self, msg):
        self.odom = msg

    def on_scan_receipt(self, msg):
        self.scans_received += 1

    def on_map(self, msg):
        self.map_info = msg

    def on_cloud(self, msg):
        self.points_received += 1
        stamp = seconds(msg.header.stamp)
        if self.args.mode == "mapping" and stamp - self.last_cloud >= 1.0:
            self.pending.append(("cloud", None, msg))
            self.last_cloud = stamp

    def read_truth(self):
        while True:
            position = self.truth_stream.tell()
            line = self.truth_stream.readline()
            if not line or not line.endswith("\n"):
                self.truth_stream.seek(position)
                break
            self.truth.append(json.loads(line))

    def synchronized_truth(self, stamp):
        if not self.truth or stamp > self.truth[-1]["stamp_s"]:
            return None
        near = min(self.truth, key=lambda item: abs(item["stamp_s"] - stamp))
        delta = abs(near["stamp_s"] - stamp)
        return (near, delta) if delta <= 0.05 else False

    def drain(self):
        for _ in range(len(self.pending)):
            kind, case, msg = self.pending.popleft()
            match = self.synchronized_truth(seconds(msg.header.stamp))
            if match is None:
                self.pending.append((kind, case, msg))
                continue
            if match is False:
                if case:
                    self.dropped[case] += 1
                continue
            truth, delta = match
            if kind == "cloud":
                try:
                    extrinsic = self.tf.lookup_transform(
                        "base_footprint", msg.header.frame_id, rclpy.time.Time()
                    ).transform
                except Exception:
                    self.pending.append((kind, case, msg))
                    continue
                p, q = extrinsic.translation, extrinsic.rotation
                pose = matrix(truth["xyz"], truth["xyzw"]) @ matrix([p.x, p.y, p.z], [q.x, q.y, q.z, q.w])
                xyz = point_cloud2.read_points_numpy(msg, field_names=("x", "y", "z"), skip_nans=True)
                valid = xyz[np.isfinite(xyz).all(axis=1) & (np.linalg.norm(xyz, axis=1) > 0.30)]
                self.clouds.append(valid.astype(np.float32))
                self.poses.append(pose)
                self.cloud_stamps.append(seconds(msg.header.stamp))
            else:
                pose = msg.pose.pose
                identity = (msg.header.stamp.sec, msg.header.stamp.nanosec, pose.position.x, pose.position.y,
                            pose.position.z, pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w)
                if identity in self.seen_poses[case]:
                    continue
                self.seen_poses[case].add(identity)
                tx, ty, _ = truth["xyz"]
                qx, qy, qz, qw = truth["xyzw"]
                truth_yaw = math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
                est_yaw = yaw(pose.orientation)
                error = math.hypot(pose.position.x - tx, pose.position.y - ty)
                row = [
                    seconds(msg.header.stamp),
                    tx,
                    ty,
                    truth_yaw,
                    pose.position.x,
                    pose.position.y,
                    est_yaw,
                    error,
                    wrap(est_yaw - truth_yaw),
                    delta,
                ]
                self.writers[case].writerow(row)
                self.files[case].flush()
                self.rows[case].append(row)
                if case in self.pose3d_writers:
                    q = pose.orientation
                    self.pose3d_writers[case].writerow([row[0], *truth["xyz"], *truth["xyzw"],
                                                       pose.position.x, pose.position.y, pose.position.z,
                                                       q.x, q.y, q.z, q.w, delta])
                    self.pose3d_files[case].flush()
                if case == self.case_names[0] and self.odom and not self.cases[case].get("native_map_odom_tf"):
                    odom = self.odom.pose.pose
                    oyaw = yaw(odom.orientation)
                    dyaw = wrap(est_yaw - oyaw)
                    c, s = math.cos(dyaw), math.sin(dyaw)
                    self.map_transform = (
                        pose.position.x - c * odom.position.x + s * odom.position.y,
                        pose.position.y - s * odom.position.x - c * odom.position.y,
                        dyaw,
                    )

    def broadcast(self):
        if self.map_transform and self.args.mode == "localization":
            x, y, angle = self.map_transform
            msg = TransformStamped()
            msg.header.frame_id, msg.child_frame_id = "map", "odom"
            msg.header.stamp = self.node.get_clock().now().to_msg()
            msg.transform.translation.x, msg.transform.translation.y = x, y
            msg.transform.rotation.z, msg.transform.rotation.w = math.sin(angle / 2), math.cos(angle / 2)
            self.broadcaster.sendTransform(msg)

    def run_loop(self):
        print("Keyboard: i/k forward/back; j/l yaw; u/o lateral; space stop; q finish.", flush=True)
        previous = termios.tcgetattr(sys.stdin) if sys.stdin.isatty() else None
        if previous:
            tty.setcbreak(sys.stdin.fileno())
        try:
            while rclpy.ok():
                rclpy.spin_once(self.node, timeout_sec=0.03)
                self.read_truth()
                self.drain()
                self.broadcast()
                sim = self.node.get_clock().now().nanoseconds * 1e-9
                wall = time.monotonic()
                if (
                    (self.points_received or (self.simple_probe and self.scans_received))
                    and self.odom
                    and self.truth
                    and self.map_info
                    and all(self.rows[case] for case in self.case_names)
                    and not (self.run / "ready.json").exists()
                ):
                    (self.run / "ready.json").write_text(
                        json.dumps(
                            {
                                "state": "LIVE_READY",
                                "points_frames": self.points_received,
                                "truth_stamp_s": self.truth[-1]["stamp_s"],
                            }
                        )
                    )
                    print("LIVE_READY: real Gazebo and RViz; independent truth synchronized.", flush=True)
                if (self.run / "recording.started").exists() and self.started_sim is None:
                    self.started_sim, self.start_record_wall = sim, wall
                if previous and select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1)
                    self.keys = Twist()
                    if key == "q":
                        break
                    if key in "ik":
                        self.keys.linear.x = 0.25 if key == "i" else -0.25
                    if key in "uo":
                        self.keys.linear.y = 0.20 if key == "u" else -0.20
                    if key in "jl":
                        self.keys.angular.z = 0.35 if key == "j" else -0.35
                    self.last_control = wall
                if not self.args.auto:
                    self.command_pub.publish(self.keys if wall - self.last_control < 0.4 else Twist())
                if wall - self.last_print > 1:
                    rates = self.points_received / max(wall - self.started_wall, 0.01)
                    errors = " ".join(
                        f"{case}={rows[-1][7]:.3f}m" for case, rows in self.rows.items() if rows
                    )
                    print(
                        f"LIVE sim={sim:.1f}s cloud_frames={self.points_received} wall_cloud_rate={rates:.2f}Hz "
                        f"mapped_scans={len(self.clouds)} matched_truth={len(self.truth)} {errors}",
                        flush=True,
                    )
                    self.last_print = wall
                if self.started_sim is not None and sim - self.started_sim >= self.args.duration:
                    break
                if (
                    self.started_sim is not None
                    and wall - self.start_record_wall > self.args.duration * 4 + 60
                ):
                    raise RuntimeError("Simulation did not advance within the wall-time limit")
                if (self.run / "STOP").exists():
                    break
        except Exception as error:
            self.failure = str(error)
            raise
        finally:
            if previous:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, previous)
            self.command_pub.publish(Twist())
            self.save()

    def save(self):
        if self.clouds:
            archive = {f"scan_{i:04d}": cloud for i, cloud in enumerate(self.clouds)}
            archive["poses"] = np.asarray(self.poses)
            archive["stamps"] = np.asarray(self.cloud_stamps)
            np.savez_compressed(self.run / "mapping-clouds.npz", **archive)
        report = {
            "kind": "live_native_ui_session",
            "status": "failed" if self.failure else "completed",
            "failure": self.failure,
            "mode": self.args.mode,
            "points_received": self.points_received,
            "scans_received": self.scans_received,
            "mapping_frames": len(self.clouds),
            "truth_source": "Gazebo Pose_V named omni_car, top-level simulation timestamp",
            "truth_used_for": "evaluation/display; provided poses only in controlled mapping A",
            "score_alignment": "none; native author-derived maps and truth share world/map coordinates",
            "score_sampling": "native estimator pose updates; nearest truth within 0.05 simulation seconds",
            "cases": {},
        }
        for case, rows in self.rows.items():
            array = np.asarray(rows)
            if len(rows):
                selected = array[array[:, 0] >= array[0, 0] + 5]
                report["cases"][case] = {
                    "samples": len(rows),
                    "dropped_unsynchronized": self.dropped[case],
                    "position_rmse_m": float(np.sqrt(np.mean(array[:, 7] ** 2))),
                    "yaw_rmse_deg": float(np.sqrt(np.mean(array[:, 8] ** 2)) * 180 / math.pi),
                    "post_warmup_5s_samples": len(selected),
                    "post_warmup_5s_position_rmse_m": float(np.sqrt(np.mean(selected[:, 7] ** 2)))
                    if len(selected)
                    else None,
                    "position_p95_m": float(np.percentile(array[:, 7], 95)),
                }
            else:
                report["cases"][case] = {
                    "status": "no_scored_samples",
                    "dropped_unsynchronized": self.dropped[case],
                }
            self.files[case].close()
            if case in self.pose3d_files:
                self.pose3d_files[case].close()
        if self.map_info:
            msg = self.map_info
            cells = np.asarray(msg.data, dtype=np.int16).reshape(msg.info.height, msg.info.width)
            image = np.where(cells < 0, 205, np.where(cells >= 65, 0, 254)).astype(np.uint8)
            with (self.run / "slam-map.pgm").open("wb") as stream:
                stream.write(f"P5\n{msg.info.width} {msg.info.height}\n255\n".encode())
                stream.write(np.flipud(image).tobytes())
            report["observed_map"] = {
                "width": msg.info.width,
                "height": msg.info.height,
                "resolution_m": msg.info.resolution,
                "known_cells": int(np.sum(cells >= 0)),
            }
        (self.run / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
        marker = "failed.json" if self.failure else "finished.json"
        (self.run / marker).write_text(
            json.dumps(
                {
                    "state": "FAILED" if self.failure else "FINISHED",
                    "failure": self.failure,
                    "wall_time": time.time(),
                }
            )
        )
        print(json.dumps(report, indent=2), flush=True)
        self.node.destroy_node()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--mode", choices=["mapping", "localization"], required=True)
    parser.add_argument("--duration", type=float, default=90)
    parser.add_argument("--cases", default="")
    parser.add_argument("--auto", action="store_true")
    args = parser.parse_args()
    rclpy.init()
    observer = Observer(args)
    try:
        observer.run_loop()
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
