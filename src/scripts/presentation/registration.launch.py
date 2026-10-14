"""Unmodified upstream NDT/GICP localizer on the live Sim2Real 3D sensor."""
import json
import math
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start(context):
    cases = json.loads(Path(LaunchConfiguration("cases_file").perform(context)).read_text())
    actions = []
    for name, case in cases.items():
        pose = case["initial_pose"]
        params = {
            "use_sim_time": True, "registration_method": case["localizer"],
            "global_frame_id": "map", "odom_frame_id": "odom", "base_frame_id": "base_footprint",
            "use_pcd_map": True, "map_path": case["map_pcd"], "set_initial_pose": True,
            "initial_pose_x": pose["x"], "initial_pose_y": pose["y"], "initial_pose_z": 0.0,
            "initial_pose_qx": 0.0, "initial_pose_qy": 0.0,
            "initial_pose_qz": math.sin(pose["yaw"] / 2), "initial_pose_qw": math.cos(pose["yaw"] / 2),
            "use_odom": True, "use_twist_prediction": False, "use_imu": False,
            "use_continuous_time_deskew": False, "enable_map_odom_tf": True,
            "enable_timer_publishing": False, "voxel_leaf_size": .15, "scan_min_range": .30,
            "scan_max_range": 12.0, "scan_period": .1, "ndt_resolution": .5,
            "ndt_step_size": .1, "ndt_num_threads": 2, "ndt_max_iterations": 35,
            "transform_epsilon": .001, "score_threshold": 2.0,
            "gicp_max_correspondence_distance": 1.0, "enable_debug": True,
        }
        actions.extend([
            Node(package="nav2_map_server", executable="map_server", name="map_server", namespace=name,
                 parameters=[{"use_sim_time": True, "yaml_filename": case["map_yaml"], "frame_id": "map"}]),
            Node(package="lidar_localization_ros2", executable="lidar_localization_node",
                 name="lidar_localization", namespace=name, parameters=[params], output="screen",
                 remappings=[("cloud", "/points"), ("/cloud", "/points"),
                             ("odom", "/omni_drive_controller/odom"), ("/odom", "/omni_drive_controller/odom")]),
            Node(package="lidar_localization_ros2", executable="start_lifecycle_node.py",
                 arguments=[f"/{name}/lidar_localization"], output="screen"),
            Node(package="nav2_lifecycle_manager", executable="lifecycle_manager", name="map_lifecycle", namespace=name,
                 parameters=[{"use_sim_time": True, "autostart": True, "node_names": ["map_server"]}]),
        ])
    return actions


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument("cases_file"), OpaqueFunction(function=start)])
