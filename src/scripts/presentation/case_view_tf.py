"""Isolate each live AMCL display's TF without changing any localizer inputs."""
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import rclpy
from scipy.spatial.transform import Rotation
from geometry_msgs.msg import PoseStamped, PoseWithCovarianceStamped, TransformStamped
from nav_msgs.msg import Odometry, Path as RosPath
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from tf2_msgs.msg import TFMessage


def yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))


class Views:
    def __init__(self, run):
        self.node = rclpy.create_node("independent_live_rviz_frames")
        self.node.set_parameters([rclpy.parameter.Parameter("use_sim_time", value=True)])
        self.run, self.odom = run, None
        self.specs = json.loads((run / "views.json").read_text())
        self.transforms, self.paths, self.pubs = {}, {}, {}
        self.log = (run / "view-updates.jsonl").open("w")
        durable = QoSProfile(depth=10, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        for case in self.specs:
            self.pubs[case] = (self.node.create_publisher(TFMessage, f"/{case}/view/tf", 100),
                               self.node.create_publisher(TFMessage, f"/{case}/view/tf_static", durable),
                               self.node.create_publisher(RosPath, f"/{case}/view/path", 5))
            self.paths[case] = RosPath()
            self.paths[case].header.frame_id = "map"
            self.node.create_subscription(PoseWithCovarianceStamped, self.specs[case]["pose_topic"],
                                          lambda msg, name=case: self.pose(name, msg), 20)
        self.node.create_subscription(Odometry, "/omni_drive_controller/odom", self.on_odom, 30)
        self.node.create_subscription(TFMessage, "/tf", lambda msg: self.relay(msg, 0), 100)
        self.node.create_subscription(TFMessage, "/tf_static", lambda msg: self.relay(msg, 1), durable)
        self.node.create_timer(.05, self.broadcast)

    def on_odom(self, msg):
        self.odom = msg

    def relay(self, msg, index):
        # Exclude global Raw map alignment. Each RViz receives its own alignment.
        clean = TFMessage(transforms=[part for part in msg.transforms if part.header.frame_id != "map"])
        if clean.transforms:
            for pubs in self.pubs.values():
                pubs[index].publish(clean)

    def pose(self, case, msg):
        if self.odom is None:
            return
        pose, odom = msg.pose.pose, self.odom.pose.pose
        angle = yaw(pose.orientation)-yaw(odom.orientation)
        c, s = math.cos(angle), math.sin(angle)
        self.transforms[case] = (pose.position.x-c*odom.position.x+s*odom.position.y,
                                 pose.position.y-s*odom.position.x-c*odom.position.y, angle)
        if self.specs[case].get("dimension") == "3d" or self.specs[case].get("full_pose_display_tf"):
            def transform(value):
                p, q = value.position, value.orientation
                result = np.eye(4)
                result[:3, :3] = Rotation.from_quat([q.x, q.y, q.z, q.w]).as_matrix()
                result[:3, 3] = [p.x, p.y, p.z]
                return result
            alignment = transform(pose) @ np.linalg.inv(transform(odom))
            self.transforms[case] = (alignment[:3, 3], Rotation.from_matrix(alignment[:3, :3]).as_quat())
        path = self.paths[case]
        point = PoseStamped(header=copy.deepcopy(msg.header), pose=copy.deepcopy(pose))
        path.header.stamp = msg.header.stamp
        path.poses.append(point)
        self.pubs[case][2].publish(path)
        self.log.write(json.dumps({"case": case, "stamp_s": msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9,
                                   "updates": len(path.poses), "map_topic": self.specs[case]["map_topic"],
                                   "pose_topic": self.specs[case]["pose_topic"], "tf_topic": f"/{case}/view/tf"})+"\n")
        self.log.flush()
        if len(self.transforms) == len(self.specs):
            (self.run / "views-ready.json").write_text(json.dumps({"live_cases": list(self.transforms)}))

    def broadcast(self):
        for case, alignment in self.transforms.items():
            transform = TransformStamped()
            transform.header.frame_id, transform.child_frame_id = "map", "odom"
            transform.header.stamp = self.node.get_clock().now().to_msg()
            if self.specs[case].get("dimension") == "3d" or self.specs[case].get("full_pose_display_tf"):
                xyz, q = alignment
                transform.transform.translation.x, transform.transform.translation.y, transform.transform.translation.z = map(float, xyz)
                transform.transform.rotation.x, transform.transform.rotation.y, transform.transform.rotation.z, transform.transform.rotation.w = map(float, q)
            else:
                x, y, angle = alignment
                transform.transform.translation.x, transform.transform.translation.y = x, y
                transform.transform.rotation.z, transform.transform.rotation.w = math.sin(angle/2), math.cos(angle/2)
            self.pubs[case][0].publish(TFMessage(transforms=[transform]))


def main():
    rclpy.init()
    views = Views(Path(sys.argv[1]))
    try:
        rclpy.spin(views.node)
    finally:
        views.log.close()
        views.node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
