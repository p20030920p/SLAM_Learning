"""Render the actual repository URDF in a dedicated, isolated RViz window."""

import argparse
from pathlib import Path
import subprocess
import time

import rclpy
from sensor_msgs.msg import JointState
import yaml


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    source = args.repo / "config/robot_profiles/omni-3d-v1/omni_car_lidar3d.urdf"
    params = args.output / "robot.yaml"
    params.write_text(yaml.safe_dump({"/**": {"ros__parameters": {"robot_description": source.read_text()}}}))
    config = {
        "Panels": [],
        "Visualization Manager": {
            "Class": "",
            "Displays": [
                {
                    "Class": "rviz_default_plugins/RobotModel",
                    "Name": "Actual omni-3d-v1 URDF",
                    "Enabled": True,
                    "Description Source": "Topic",
                    "Description Topic": {
                        "Value": "/robot_description",
                        "Durability Policy": "Transient Local",
                        "Reliability Policy": "Reliable",
                        "Depth": 1,
                    },
                    "Visual Enabled": True,
                    "Collision Enabled": False,
                    "Alpha": 1.0,
                }
            ],
            "Global Options": {
                "Fixed Frame": "base_footprint",
                "Background Color": "228; 234; 240",
                "Frame Rate": 15,
            },
            "Views": {
                "Current": {
                    "Class": "rviz_default_plugins/Orbit",
                    "Target Frame": "base_footprint",
                    "Distance": 1.15,
                    "Pitch": 0.45,
                    "Yaw": 0.85,
                    "Focal Point": {"X": 0.0, "Y": 0.0, "Z": 0.15},
                }
            },
            "Tools": [],
        },
        "Window Geometry": {
            "Width": 1000,
            "Height": 760,
            "X": 0,
            "Y": 0,
            "Hide Left Dock": True,
            "Hide Right Dock": True,
        },
    }
    rviz = args.output / "robot.rviz"
    rviz.write_text(yaml.safe_dump(config, sort_keys=False))
    log = (args.output / "renderer.log").open("w")
    children = [
        subprocess.Popen(
            [
                "ros2",
                "run",
                "robot_state_publisher",
                "robot_state_publisher",
                "--ros-args",
                "--params-file",
                str(params),
            ],
            stdout=log,
            stderr=log,
        ),
        subprocess.Popen(
            ["rviz2", "-d", str(rviz), "-t", "SLAM URDF - Actual robot model"], stdout=log, stderr=log
        ),
    ]
    rclpy.init()
    node = rclpy.create_node("urdf_screenshot_joint_states")
    pub = node.create_publisher(JointState, "/joint_states", 10)
    try:
        while not (args.output / "STOP").exists() and all(p.poll() is None for p in children):
            msg = JointState()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.name = ["front_wheel_joint", "left_wheel_joint", "right_wheel_joint"]
            msg.position = [0.0] * 3
            pub.publish(msg)
            rclpy.spin_once(node, timeout_sec=0.1)
            time.sleep(0.05)
    finally:
        for child in children:
            child.terminate()
            child.wait(timeout=10)
        node.destroy_node()
        rclpy.shutdown()
        log.close()


if __name__ == "__main__":
    main()
