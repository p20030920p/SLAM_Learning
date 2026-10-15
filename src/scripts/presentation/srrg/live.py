"""ROS2 transport/display for the actual author Mapper2D worker, not a replacement.

Native /scan and wheel odometry only; known start anchor + measured TF. Truth is
written independently by the existing observer and used only after the run.
"""

import copy
import json
import math
from pathlib import Path
import socket
import sys
import time
from datetime import datetime

import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from sensor_msgs.msg import LaserScan, PointCloud2
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from tf2_ros import Buffer, TransformListener, TransformBroadcaster


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def T(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, x], [s, c, y], [0, 0, 1.0]])


class Live:
    def __init__(self, run):
        self.run = run
        self.runtime = json.loads((run / "runtime.json").read_text())
        self.node = rclpy.create_node("srrg_native_mapper_transport")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self.node)
        self.broadcast = TransformBroadcaster(self.node)
        self.odom = None
        self.last = -1e9
        self.started = None
        self.raw = []
        self.inputs = []
        self.snapshots = {}
        self.times = []
        self.last_snapshot = -1e9
        self.last_status = None
        self.log = (run / "srrg-frames.jsonl").open("w")
        self.input_log = (run / "srrg-inputs.jsonl").open("w")
        self.socket = socket.create_connection(("127.0.0.1", 19192), timeout=10)
        self.socket.settimeout(15)
        self.io = self.socket.makefile("rwb")
        config = {"run": str(run), "graph_merge": False}
        if self.runtime.get("srrg_prior"):
            config["prior"] = self.runtime["srrg_prior"]
        self.io.write((json.dumps(config) + "\n").encode())
        self.io.flush()
        self.map_pub = self.node.create_publisher(
            OccupancyGrid, "/map", QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        )
        self.clean_pub = self.node.create_publisher(PointCloud2, "/srrg/clean", 1)
        self.raw_pub = self.node.create_publisher(PointCloud2, "/srrg/raw", 1)
        self.scan_pub = self.node.create_publisher(LaserScan, "/srrg/scan_used", qos_profile_sensor_data)
        self.node.create_subscription(
            Odometry, "/omni_drive_controller/odom", self.on_odom, qos_profile_sensor_data
        )
        self.node.create_subscription(LaserScan, "/scan", self.on_scan, qos_profile_sensor_data)

    def on_odom(self, msg):
        self.odom = msg

    def exchange(self, line):
        self.io.write((line + "\n").encode())
        self.io.flush()
        reply = self.io.readline()
        if not reply:
            raise RuntimeError("Native mapper produced no output; see author stderr")
        return json.loads(reply)

    def on_scan(self, msg):
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        if self.odom is None or stamp - self.last < 0.199:
            return
        os = self.odom.header.stamp.sec + self.odom.header.stamp.nanosec * 1e-9
        if abs(os - stamp) > 0.1:
            return
        try:
            e = self.tf.lookup_transform("base_footprint", msg.header.frame_id, rclpy.time.Time()).transform
        except Exception:
            return
        self.last = stamp
        if self.started is None and (self.run / "recording.started").exists():
            self.started = stamp
        elapsed = stamp - self.started if self.started is not None else None
        values = np.array(msg.ranges, dtype=float)
        limited = self.runtime["scene"] == "corridor" and (elapsed is None or elapsed < 50)
        if limited:
            target = np.linspace(-2 * math.pi / 3, 2 * math.pi / 3, 72)
            ids = np.rint((target - msg.angle_min) / msg.angle_increment).astype(int)
            selected = np.zeros(len(values), bool)
            selected[np.clip(ids, 0, len(values) - 1)] = True
            values[~selected | (values > 3.5)] = np.inf
        # Invalid bins remain invalid. No ray interpolation or range invention.
        native = np.where(np.isfinite(values), values, 0.0)
        used = copy.deepcopy(msg)
        used.ranges = values.tolist()
        self.scan_pub.publish(used)
        p = self.odom.pose.pose
        data = [
            stamp,
            p.position.x,
            p.position.y,
            yaw(p.orientation),
            e.translation.x,
            e.translation.y,
            yaw(e.rotation),
            msg.angle_min,
            msg.angle_max,
            msg.angle_increment,
            msg.range_min,
            msg.range_max,
            len(values),
            *native,
        ]
        before = time.monotonic()
        reply = self.exchange("S " + " ".join(map(str, data)))
        latency = time.monotonic() - before
        offset = T(e.translation.x, e.translation.y, yaw(e.rotation))
        self.offset = offset
        self.anchor = T(*self.runtime["spawn"]) @ offset
        laser_pose = self.anchor @ T(*reply["pose"])
        base_pose = laser_pose @ np.linalg.inv(offset)
        clean = np.asarray(reply.pop("points"), dtype=np.float32).reshape(-1, 2)
        clean = clean @ self.anchor[:2, :2].T + self.anchor[:2, 2]
        angles = msg.angle_min + np.arange(len(values)) * msg.angle_increment
        valid = np.isfinite(values) & (values > msg.range_min) & (values < msg.range_max) & (values > 0.45)
        xy = np.column_stack((values[valid] * np.cos(angles[valid]), values[valid] * np.sin(angles[valid])))
        self.raw.append(xy @ laser_pose[:2, :2].T + laser_pose[:2, 2])
        frame = {
            "stamp_s": stamp,
            "elapsed_s": elapsed,
            "range_max_effective_m": 3.5 if limited else msg.range_max,
            "finite_beams": int(valid.sum()),
            "phase": "limited" if limited else "full",
            "native_latency_s": latency,
            **reply,
            "base_pose": [base_pose[0, 2], base_pose[1, 2], math.atan2(base_pose[1, 0], base_pose[0, 0])],
            "clean_points": len(clean),
        }
        if elapsed is not None:
            frame["recording_wall_elapsed_s"] = (
                time.time()
                - datetime.fromisoformat((self.run / "recording.started").read_text().strip()).timestamp()
            )
        inp = {
            "stamp_s": stamp,
            "odom_stamp_s": os,
            "ranges": native.tolist(),
            "angle_min": msg.angle_min,
            "angle_increment": msg.angle_increment,
            "laser_tf_xyz": [e.translation.x, e.translation.y, e.translation.z],
            "laser_tf_xyzw": [e.rotation.x, e.rotation.y, e.rotation.z, e.rotation.w],
            "estimated_laser_pose": laser_pose.tolist(),
            "wheel_odom": [p.position.x, p.position.y, yaw(p.orientation)],
        }
        self.input_log.write(json.dumps(inp) + "\n")
        self.input_log.flush()
        self.log.write(json.dumps(frame) + "\n")
        self.log.flush()
        if stamp - self.last_snapshot >= 1:
            self.times.append(stamp)
            self.snapshots[f"clean_{len(self.times)-1:04d}"] = clean.astype(np.float32)
            self.snapshots[f"raw_{len(self.times)-1:04d}"] = np.concatenate(self.raw).astype(np.float32)
            self.last_snapshot = stamp
        self.publish(clean, np.concatenate(self.raw), base_pose, msg.header)
        if reply["status"] != self.last_status:
            print("SRRG STATUS: " + json.dumps(frame), flush=True)
            self.last_status = reply["status"]
        if len(self.raw) % 5 == 0:
            print(
                f"SRRG native t={stamp:.1f}s phase={frame['phase']} status={reply['status']} graph={reply['vertices']} clean={len(clean)} raw={sum(map(len,self.raw))} callback={latency:.3f}s",
                flush=True,
            )

    def publish(self, clean, raw, base, header):
        h = Header()
        h.frame_id = "map"
        h.stamp = header.stamp
        for pub, points in ((self.clean_pub, clean), (self.raw_pub, raw)):
            pub.publish(point_cloud2.create_cloud_xyz32(h, np.column_stack((points, np.zeros(len(points))))))
        grid = OccupancyGrid()
        grid.header = h
        grid.info.resolution = 0.05
        grid.info.width = 320
        grid.info.height = 440
        grid.info.origin.position.x = -2.0
        grid.info.origin.position.y = -9.0
        grid.info.origin.orientation.w = 1.0
        cells = np.full((440, 320), -1, dtype=np.int8)
        ids = np.floor((clean - [-2, -9]) / 0.05).astype(int)
        valid = (ids[:, 0] >= 0) & (ids[:, 0] < 320) & (ids[:, 1] >= 0) & (ids[:, 1] < 440)
        cells[ids[valid, 1], ids[valid, 0]] = 100
        grid.data = cells.ravel().tolist()
        self.map_pub.publish(grid)
        op = self.odom.pose.pose
        tf = base @ np.linalg.inv(T(op.position.x, op.position.y, yaw(op.orientation)))
        tr = TransformStamped()
        tr.header = h
        tr.child_frame_id = "odom"
        tr.transform.translation.x = float(tf[0, 2])
        tr.transform.translation.y = float(tf[1, 2])
        a = math.atan2(tf[1, 0], tf[0, 0])
        tr.transform.rotation.z = math.sin(a / 2)
        tr.transform.rotation.w = math.cos(a / 2)
        self.broadcast.sendTransform(tr)

    def finish(self):
        reply = self.exchange("F")
        points = np.asarray(reply["points"]).reshape(-1, 2)
        points = points @ self.anchor[:2, :2].T + self.anchor[:2, 2]
        np.save(self.run / "srrg-final.npy", points.astype(np.float32))
        np.save(self.run / "srrg-raw.npy", np.concatenate(self.raw).astype(np.float32))
        np.savez_compressed(self.run / "srrg-snapshots.npz", stamps=np.array(self.times), **self.snapshots)
        self.log.close()
        self.input_log.close()
        self.io.close()
        self.socket.close()
        (self.run / "srrg-finished.json").write_text(
            json.dumps(
                {"frames": len(self.raw), "snapshots": len(self.times), "final_vertices": reply["vertices"]}
            )
        )


if __name__ == "__main__":
    rclpy.init()
    live = Live(Path(sys.argv[1]))
    try:
        while rclpy.ok() and not (live.run / "finished.json").exists() and not (live.run / "STOP").exists():
            rclpy.spin_once(live.node, timeout_sec=0.05)
        live.finish()
    except Exception as error:
        (live.run / "srrg-failed.json").write_text(
            json.dumps({"error": str(error), "last_stamp_s": live.last})
        )
        # Preserve every completed native output, including a failed run's prefix.
        if live.snapshots:
            np.savez_compressed(
                live.run / "srrg-snapshots.npz", stamps=np.array(live.times), **live.snapshots
            )
            last = live.snapshots[f"clean_{len(live.times)-1:04d}"]
            np.save(live.run / "srrg-partial.npy", last)
        raise
    finally:
        live.node.destroy_node()
        rclpy.shutdown()
