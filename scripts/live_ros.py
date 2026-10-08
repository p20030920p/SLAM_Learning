"""Local WSL ROS receiver, algorithm supervisor and measured live diagnostics."""
import argparse
from array import array as byte_array
from collections import deque
import json
import os
from pathlib import Path
import secrets
import signal
import socket
import struct
import subprocess
import threading
import time
import traceback
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Odometry, Path as PathMessage
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from std_msgs.msg import String
from visualization_msgs.msg import Marker
from tf2_ros import StaticTransformBroadcaster, TransformBroadcaster
from rtabmap_msgs.msg import OdomInfo, MapData
from live_transport import receive
from live_metrics import match_observations
from record_rviz import RvizRecording

CAMERA = "/physical/camera"


def stamp(ns):
    from builtin_interfaces.msg import Time
    return Time(sec=ns // 1000000000, nanosec=ns % 1000000000)


def cloud_message(xyzi, frame, ns, rgb=False):
    value = PointCloud2()
    value.header.frame_id = frame
    value.header.stamp = stamp(ns)
    value.height = 1
    value.width = len(xyzi)
    value.is_bigendian = False
    value.is_dense = True
    names = ("x", "y", "z", "rgb" if rgb else "intensity")
    value.fields = [PointField(name=name, offset=i * 4, datatype=PointField.FLOAT32, count=1)
                    for i, name in enumerate(names)]
    value.point_step = 16
    value.row_step = 16 * len(xyzi)
    value.data = byte_array("B", np.asarray(xyzi, dtype="<f4").tobytes())
    return value


class Receiver(Node):
    def __init__(self, config, session):
        super().__init__("physical_live_bridge")
        self.config = config
        self.session = session
        self.images = {}
        for key in ("color", "depth", "depth_color", "left", "right"):
            self.images[key] = self.create_publisher(Image, f"{CAMERA}/{key}/image", 10)
        self.infos = {key: self.create_publisher(CameraInfo, f"{CAMERA}/{key}/camera_info", 10)
                      for key in ("left", "right", "color")}
        self.camera_points = self.create_publisher(PointCloud2, f"{CAMERA}/points", 5)
        self.lidar_points = self.create_publisher(PointCloud2, "/physical/lidar/points", 5)
        self.imu_raw = self.create_publisher(String, "/physical/lidar/imu_diagnostic", 20)
        self.path_pub = self.create_publisher(PathMessage, "/physical/trajectory", 5)
        self.marker_pub = self.create_publisher(Marker, "/physical/tracking", 5)
        self.status_pub = self.create_publisher(String, "/physical/status", 5)
        self.static_tf = StaticTransformBroadcaster(self)
        self.dynamic_tf = TransformBroadcaster(self)
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10) if config["algorithm"] == "kiss" else None
        self.create_subscription(Odometry, "/odom", self.odometry, 2048)
        self.create_subscription(OdomInfo, "/odom_info", self.info, 2048)
        self.create_subscription(MapData, "/rtabmap/mapData", self.map_data, 10)
        self.map_updates = 0
        self.loop_closure_ids = []
        self.path = deque(maxlen=5000)
        self.poses = []
        self.statuses = []
        self.input_stamps = []
        self.input_stamp_candidates = []
        self.inputs = 0
        self.last_state = "SENSOR PREVIEW" if config["algorithm"] == "sensor" else "WAITING FOR ODOMETRY"
        self.last_quality = {}
        self.last_path_time = 0
        self.kiss = None
        self.kiss_compute_ms = []
        self.tf_ready = False
        self.create_timer(0.5, self.publish_status)

    def map_data(self, message):
        self.map_updates += 1
        # MapData exposes graph links, not a verified loop event count.
        for link in message.graph.links:
            if link.type == 1:
                key = (link.from_id, link.to_id)
                if key not in self.loop_closure_ids:
                    self.loop_closure_ids.append(key)

    def info(self, message):
        ns = message.header.stamp.sec * 1000000000 + message.header.stamp.nanosec
        self.statuses.append(dict(stamp_ns=ns, lost=message.lost, inliers=message.inliers,
                                  features=message.features, compute_s=message.time_estimation))
        self.last_state = "LOST" if message.lost else "TRACKING"
        self.last_quality = dict(inliers=message.inliers, features=message.features,
                                 compute_ms=round(message.time_estimation * 1000, 2))

    def odometry(self, message):
        p, q = message.pose.pose.position, message.pose.pose.orientation
        ns = message.header.stamp.sec * 1000000000 + message.header.stamp.nanosec
        row = dict(stamp_ns=ns, xyz=[p.x, p.y, p.z], xyzw=[q.x, q.y, q.z, q.w],
                   covariance0=message.pose.covariance[0])
        self.poses.append(row)
        if row["covariance0"] >= 9999 or not np.isfinite(row["xyz"] + row["xyzw"]).all():
            return
        pose = PoseStamped()
        pose.header = message.header
        pose.pose = message.pose.pose
        self.path.append(pose)
        if time.monotonic() - self.last_path_time >= 0.3:
            path = PathMessage()
            path.header = message.header
            path.poses = list(self.path)
            self.path_pub.publish(path)
            self.last_path_time = time.monotonic()

    def publish_status(self):
        state = dict(state=self.last_state, algorithm=self.config["algorithm"],
                     source_observations=self.inputs, odometry_messages=len(self.poses),
                     session_type=self.config["session_type"], **self.last_quality)
        self.status_pub.publish(String(data=json.dumps(state)))
        marker = Marker()
        marker.header.frame_id = ("camera_left_optical" if self.config["sensor"] == "camera"
                                  else "physical_lidar") if self.config["algorithm"] == "sensor" else "odom"
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = "tracking_status"
        marker.id = 0
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.pose.position.z = 0.5
        marker.scale.z = 0.12
        marker.color.a = 1.0
        marker.color.r = 1.0 if self.last_state == "LOST" else 0.2
        marker.color.g = 0.2 if self.last_state == "LOST" else 1.0
        marker.text = f"LIVE {self.last_state}\n{self.config['algorithm']} | {self.inputs} inputs"
        self.marker_pub.publish(marker)

    def image(self, key, array, frame, ns, encoding):
        message = Image()
        message.header.frame_id = frame
        message.header.stamp = stamp(ns)
        message.height, message.width = array.shape[:2]
        message.encoding = encoding
        message.step = array.strides[0]
        message.is_bigendian = False
        message.data = byte_array("B", array.tobytes())
        self.images[key].publish(message)

    def camera(self, metadata, arrays):
        ns, cal = metadata["stamp_ns"], metadata["calibration"]
        native = metadata["device_timestamps_ms"]
        color_ns = ns + round((native["color"] - native["left"]) * 1000000)
        depth_ns = ns + round((native["depth"] - native["left"]) * 1000000)
        if not self.tf_ready:
            sdk = cal["sdk_left_to_color"]
            rotation = np.asarray(sdk["rotation_column_major"]).reshape(3, 3, order="F")
            translation = np.asarray(sdk["translation_m"])
            inverse = rotation.T
            transform = TransformStamped()
            transform.header.frame_id = "camera_left_optical"
            transform.child_frame_id = "camera_color_optical"
            transform.header.stamp = stamp(ns)
            transform.transform.translation.x, transform.transform.translation.y, transform.transform.translation.z = (-inverse @ translation).tolist()
            q = Rotation.from_matrix(inverse).as_quat()
            transform.transform.rotation.x, transform.transform.rotation.y, transform.transform.rotation.z, transform.transform.rotation.w = q.tolist()
            self.static_tf.sendTransform(transform)
            self.tf_ready = True
            self.calibration = cal
        for key in ("left", "right"):
            self.image(key, arrays[key], "camera_left_optical", ns, "mono8")
        self.image("color", arrays["color"], "camera_color_optical", color_ns, "bgr8")
        self.image("depth", arrays["depth"], "camera_color_optical", depth_ns, "16UC1")
        pseudo = cv2.applyColorMap(cv2.convertScaleAbs(arrays["depth"], alpha=255 / 5000),
                                  cv2.COLORMAP_TURBO)
        pseudo[arrays["depth"] == 0] = 0
        self.image("depth_color", pseudo, "camera_color_optical", depth_ns, "bgr8")
        for key in ("left", "right", "color"):
            intr = cal[key]
            message = CameraInfo()
            message.header.frame_id = "camera_color_optical" if key == "color" else "camera_left_optical"
            message.header.stamp = stamp(color_ns if key == "color" else ns)
            message.width, message.height = intr["width"], intr["height"]
            message.distortion_model = "plumb_bob"
            message.d = [0.0] * 5
            message.k = [intr["fx"], 0., intr["ppx"], 0., intr["fy"], intr["ppy"], 0., 0., 1.]
            message.r = np.eye(3).ravel().tolist()
            message.p = [intr["fx"], 0., intr["ppx"], -intr["fx"] * cal["baseline_m"] if key == "right" else 0.,
                         0., intr["fy"], intr["ppy"], 0., 0., 0., 1., 0.]
            self.infos[key].publish(message)
        z = arrays["depth"][::4, ::4].astype(np.float32) * 0.001
        v, u = np.mgrid[0:480:4, 0:640:4]
        intr = cal["color"]
        valid = (z >= 0.2) & (z <= 5)
        colors = arrays["color"][::4, ::4][valid].astype(np.uint32)
        packed = (colors[:, 2] << 16) | (colors[:, 1] << 8) | colors[:, 0]
        xyzrgb = np.column_stack(((u[valid] - intr["ppx"]) / intr["fx"] * z[valid],
                                  (v[valid] - intr["ppy"]) / intr["fy"] * z[valid],
                                  z[valid], packed.view("<f4"))).astype("<f4")
        self.camera_points.publish(cloud_message(xyzrgb, "camera_color_optical", color_ns, rgb=True))
        self.inputs += 1
        self.input_stamps.append(depth_ns if self.config["algorithm"].startswith("rgbd") else ns)
        self.input_stamp_candidates.append([color_ns, depth_ns] if self.config["algorithm"].startswith("rgbd") else [ns])

    def lidar(self, metadata, arrays):
        ns = metadata["stamp_ns"]
        self.lidar_points.publish(cloud_message(arrays["xyzi"], "physical_lidar", ns))
        self.inputs += 1
        self.input_stamps.append(ns)
        self.input_stamp_candidates.append([ns])
        if self.kiss:
            xyz = np.ascontiguousarray(arrays["xyzi"][:, :3], dtype="<f4")
            then = time.monotonic()
            self.kiss.stdin.write(struct.pack("<I", len(xyz)) + xyz.tobytes())
            self.kiss.stdin.flush()
            blob = bytearray()
            while len(blob) < 128:
                part = self.kiss.stdout.read(128 - len(blob))
                if not part:
                    raise RuntimeError("KISS worker stopped; inspect kiss-worker.log")
                blob.extend(part)
            matrix = np.frombuffer(blob, dtype="<f8").reshape(4, 4)
            q = Rotation.from_matrix(matrix[:3, :3]).as_quat()
            message = Odometry()
            message.header.frame_id = "odom"
            message.header.stamp = stamp(ns)
            message.child_frame_id = "physical_lidar"
            message.pose.pose.position.x, message.pose.pose.position.y, message.pose.pose.position.z = matrix[:3, 3].tolist()
            message.pose.pose.orientation.x, message.pose.pose.orientation.y, message.pose.pose.orientation.z, message.pose.pose.orientation.w = q.tolist()
            message.pose.covariance[0] = 9999.0 if self.inputs == 1 else 0.0
            self.odom_pub.publish(message)
            transform = TransformStamped()
            transform.header = message.header
            transform.child_frame_id = message.child_frame_id
            transform.transform.translation.x, transform.transform.translation.y, transform.transform.translation.z = matrix[:3, 3].tolist()
            transform.transform.rotation = message.pose.pose.orientation
            self.dynamic_tf.sendTransform(transform)
            self.last_state = "KISS POSE / QUALITY UNVERIFIED"
            elapsed_ms = (time.monotonic() - then) * 1000
            self.kiss_compute_ms.append(elapsed_ms)
            self.last_quality = dict(compute_ms=round(elapsed_ms, 2),
                                     covariance_note="No KISS covariance; initialization marker only")


def algorithm_parameters(config, session):
    algo = config["algorithm"]
    params = dict(frame_id="physical_lidar" if config["sensor"] == "lidar" else "camera_left_optical",
                  odom_frame_id="odom", publish_tf=True, wait_imu_to_init=False,
                  qos=1, qos_camera_info=1, topic_queue_size=20, sync_queue_size=20)
    remaps = []
    if algo == "stereo":
        executable = "stereo_odometry"
        params["approx_sync"] = False
        for side in ("left", "right"):
            remaps.extend([f"{side}/image_rect:={CAMERA}/{side}/image",
                           f"{side}/camera_info:={CAMERA}/{side}/camera_info"])
    elif algo.startswith("rgbd"):
        executable = "rgbd_odometry"
        params.update(approx_sync=True, approx_sync_max_interval=0.05, wait_for_transform=0.3)
        remaps = [f"rgb/image:={CAMERA}/color/image", f"depth/image:={CAMERA}/depth/image",
                  f"rgb/camera_info:={CAMERA}/color/camera_info"]
    else:
        executable = "icp_odometry"
        params.update({"Icp/Strategy": "0", "Icp/VoxelSize": "0.08", "Icp/PointToPlane": "true",
                       "Icp/PointToPlaneK": "20", "Icp/MaxCorrespondenceDistance": "0.3",
                       "Icp/Iterations": "30", "Odom/Deskewing": "false", "Odom/GuessMotion": "true"})
        remaps = ["scan_cloud:=/physical/lidar/points"]
    name = "physical_live_odometry"
    path = session / "odometry-parameters.yaml"
    path.write_text(json.dumps({name: {"ros__parameters": params}}, indent=2) + "\n")
    command = ["ros2", "run", "rtabmap_odom", executable, "--ros-args", "-r", f"__node:={name}",
               "--params-file", str(path)]
    for mapping in remaps:
        command += ["-r", mapping]
    return command


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    args = ap.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8-sig"))
    session = Path(config["linux_session"])
    os.environ.update(ROS_DOMAIN_ID=str(config["domain"]), ROS_LOCALHOST_ONLY="1",
                      OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    rclpy.init()
    node = Receiver(config, session)
    stop = threading.Event()
    def spin():
        while not stop.is_set() and rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.05)
    thread = threading.Thread(target=spin, daemon=True)
    thread.start()
    children, logs = [], []
    video = None
    record = dict(status="starting", sensor=config["sensor"], algorithm=config["algorithm"],
                  session_type=config["session_type"], quality_claim=False,
                  timestamp_policy="ROS stamps use WSL receipt + native per-stream offsets; Windows receipt and device times retained at source. No cross-device hardware synchronization or measured transport latency.")
    def start(command, filename, **kwargs):
        log = (session / filename).open("w")
        logs.append(log)
        stdout = kwargs.pop("stdout", log)
        child = subprocess.Popen(command, stdout=stdout, stderr=log, start_new_session=True, **kwargs)
        children.append(child)
        return child
    try:
        if config["algorithm"] not in ("sensor", "kiss"):
            start(algorithm_parameters(config, session), "odometry.log")
        if config["algorithm"] == "kiss":
            interpreter = Path(__file__).resolve().parents[1] / ".cache/kiss-venv/bin/python"
            node.kiss = start([str(interpreter), str(Path(__file__).with_name("live_kiss_worker.py"))],
                              "kiss-worker.log", stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        if config["algorithm"] == "rgbd-slam":
            params = dict(frame_id="camera_left_optical", map_frame_id="map", odom_frame_id="odom",
                          subscribe_depth=True, subscribe_odom_info=True, approx_sync=True,
                          approx_sync_max_interval=0.05, qos_image=1, qos_camera_info=1, qos_odom=1,
                          database_path=str(session / "rtabmap.db"),
                          **{"Rtabmap/DetectionRate": "1", "Grid/RangeMax": "5"})
            path = session / "mapping-parameters.yaml"
            path.write_text(json.dumps({"/rtabmap/physical_mapping": {"ros__parameters": params}}, indent=2))
            start(["ros2", "run", "rtabmap_slam", "rtabmap", "--ros-args",
                   "-r", "__node:=physical_mapping", "-r", "__ns:=/rtabmap", "--params-file", str(path),
                   "-r", f"rgb/image:={CAMERA}/color/image", "-r", f"depth/image:={CAMERA}/depth/image",
                   "-r", f"rgb/camera_info:={CAMERA}/color/camera_info",
                   "-r", "odom:=/odom", "-r", "odom_info:=/odom_info"], "mapping.log")
        family = "camera" if config["sensor"] == "camera" else "lidar"
        variant = "map" if config["algorithm"] == "rgbd-slam" else ("raw" if config["algorithm"] == "sensor" else "odom")
        rviz = Path(__file__).resolve().parents[1] / f"configs/rviz/{family}_{variant}.rviz"
        if config.get("video"):
            video = RvizRecording(session, rviz, config["domain"])
        if not config["no_gui"]:
            start(["rviz2", "-d", str(rviz)], "rviz.log")
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("127.0.0.1", config["port"]))
            server.listen(1)
            server.settimeout(30)
            print("ROS LIVE listener ready", flush=True)
            with server.accept()[0] as connection:
                connection.settimeout(10)
                hello, _ = receive(connection)
                if hello.get("kind") != "hello" or not secrets.compare_digest(hello.get("token", ""), config["token"]):
                    raise ValueError("Local bridge authentication failed")
                record["status"] = "streamed"
                while True:
                    try:
                        metadata, arrays = receive(connection)
                    except EOFError:
                        break
                    metadata["windows_receipt_ns"] = metadata.get("stamp_ns")
                    metadata["stamp_ns"] = node.get_clock().now().nanoseconds
                    if metadata["kind"] == "camera":
                        node.camera(metadata, arrays)
                    elif metadata["kind"] == "lidar":
                        node.lidar(metadata, arrays)
                    elif metadata["kind"] == "imu_raw":
                        node.imu_raw.publish(String(data=json.dumps(metadata)))
                    failed = [p.returncode for p in children if p.poll() is not None and p.returncode != 0]
                    if failed:
                        raise RuntimeError(f"Owned algorithm/GUI process stopped: {failed}; inspect logs")
                    if video:
                        video.check()
        time.sleep(2)
        if not node.inputs:
            raise RuntimeError("No sensor observations received; inspect live-capture.json")
        if config["algorithm"] != "sensor" and not node.poses:
            raise RuntimeError("No odometry messages received; inspect odometry.log or kiss-worker.log")
    except KeyboardInterrupt:
        record["status"] = "stopped_by_operator"
    except Exception as error:
        record.update(status="failed", error=repr(error), traceback=traceback.format_exc())
    finally:
        if video:
            record["video"] = video.close()
            if record["video"]["status"] == "failed":
                record["status"] = "failed"
        for child in reversed(children):
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
                try:
                    child.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
        stop.set()
        thread.join(timeout=2)
        record.update(source_observations=node.inputs, odometry_messages=len(node.poses),
                      status_messages=len(node.statuses), map_data_updates=node.map_updates,
                      graph_global_closure_links=node.loop_closure_ids,
                      native_calibration=getattr(node, "calibration", None))
        # RGB-D approximate synchronization can stamp its output with either
        # contributing image. Match either recorded stamp within 1 us, once.
        matched = match_observations(node.input_stamp_candidates, [p["stamp_ns"] for p in node.poses])
        record["pose_output_fraction"] = len(matched) / len(node.input_stamps) if node.input_stamps else None
        record["pose_matching_policy"] = "One output per input; RGB-D color or depth stamp, stereo/lidar stamp; tolerance 1 microsecond. Coverage includes lost poses; lost separately reported."
        record["lost_status_fraction"] = sum(p["lost"] for p in node.statuses) / len(node.statuses) if node.statuses else None
        if node.input_stamps:
            steady = {i for i,s in enumerate(node.input_stamps) if s >= node.input_stamps[0] + 2000000000}
            record["pose_output_fraction_after_first_2s"] = len(steady & matched) / len(steady) if steady else None
            if len(node.input_stamps) > 1:
                intervals = np.diff(node.input_stamps) * 1e-9
                record["ros_input_hz"] = float(1 / np.mean(intervals))
                record["ros_input_gap_p95_ms"] = float(np.percentile(intervals, 95) * 1000)
        if node.statuses:
            compute = np.asarray([p["compute_s"] for p in node.statuses]) * 1000
            record["odometry_compute_ms"] = dict(p50=float(np.median(compute)), p95=float(np.percentile(compute, 95)))
        if node.kiss_compute_ms:
            record["kiss_worker_compute_ms"] = dict(p50=float(np.median(node.kiss_compute_ms)), p95=float(np.percentile(node.kiss_compute_ms, 95)))
        valid = [p for p in node.poses if p["covariance0"] < 9999 and np.isfinite(p["xyz"] + p["xyzw"]).all()]
        valid_matched = match_observations(node.input_stamp_candidates, [p["stamp_ns"] for p in valid])
        record["valid_pose_output_fraction"] = (len(valid_matched) / len(node.input_stamps)
                                               if node.input_stamps and config["algorithm"] not in ("sensor", "kiss") else None)
        record["valid_pose_output_fraction_after_first_2s"] = (len(steady & valid_matched) / len(steady)
                                                              if node.input_stamps and steady and config["algorithm"] not in ("sensor", "kiss") else None)
        if len(valid) > 1:
            xyz = np.asarray([p["xyz"] for p in valid])
            q = np.asarray([p["xyzw"] for p in valid])
            q /= np.linalg.norm(q, axis=1)[:, None]
            displacement = np.linalg.norm(xyz - xyz[0], axis=1)
            angle = np.degrees(2 * np.arccos(np.clip(np.abs(q @ q[0]), 0, 1)))
            record.update(translation_excursion_max_m=float(displacement.max()),
                          translation_endpoint_separation_m=float(displacement[-1]),
                          rotation_excursion_max_deg=float(angle.max()),
                          estimated_path_length_m=float(np.linalg.norm(np.diff(xyz, axis=0), axis=1).sum()))
        record["metric_note"] = "Excursion is static deviation only for an operator-declared fixed session. No ATE/RPE; no precision pass inferred from finite poses."
        for name, value in (("live-result.json", record), ("poses.json", node.poses), ("status.json", node.statuses), ("input-stamps.json", node.input_stamp_candidates)):
            (session / name).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
        for log in logs:
            log.close()
        node.destroy_node()
        rclpy.shutdown()
    return int(record["status"] == "failed")


if __name__ == "__main__":
    raise SystemExit(main())
