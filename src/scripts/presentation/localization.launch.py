"""Parallel native AMCL controls sharing exactly the same live observations."""

import json
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_cases(context):
    cases = json.loads(Path(LaunchConfiguration("cases_file").perform(context)).read_text())
    actions = []
    for index, (name, case) in enumerate(cases.items()):
        common = {"use_sim_time": True}
        case_actions = (
            [
                Node(
                    package="nav2_map_server",
                    executable="map_server",
                    name="map_server",
                    namespace=name,
                    parameters=[{**common, "yaml_filename": case["map_yaml"], "frame_id": "map"}],
                    output="screen",
                ),
                Node(
                    package="nav2_amcl",
                    executable="amcl",
                    name="amcl",
                    namespace=name,
                    output="screen",
                    parameters=[
                        {
                            **common,
                            "robot_model_type": "nav2_amcl::OmniMotionModel",
                            "base_frame_id": "base_footprint",
                            "odom_frame_id": "odom",
                            "global_frame_id": "map",
                            "scan_topic": case.get("scan_topic", "/scan"),
                            "tf_broadcast": False,
                            "set_initial_pose": True,
                            "initial_pose": case.get("initial_pose", {"x": 8.3227, "y": 7.6812, "z": 0.0, "yaw": -1.4508}),
                            "min_particles": 500,
                            "max_particles": 2000,
                            "max_beams": 60,
                            "update_min_d": 0.05,
                            "update_min_a": 0.05,
                            "laser_min_range": 0.08,
                            "laser_max_range": 12.0,
                            "laser_model_type": "likelihood_field",
                            "laser_likelihood_max_dist": 2.0,
                            "recovery_alpha_slow": 0.0,
                            "recovery_alpha_fast": 0.0,
                            "transform_tolerance": 0.3,
                            "alpha1": 0.2,
                            "alpha2": 0.2,
                            "alpha3": 0.2,
                            "alpha4": 0.2,
                            "alpha5": 0.2,
                            "z_hit": 0.5,
                            "z_rand": 0.5,
                            "sigma_hit": 0.2,
                            "do_beamskip": False,
                        }
                    ],
                ),
                TimerAction(period=2.0, actions=[Node(
                    package="nav2_lifecycle_manager",
                    executable="lifecycle_manager",
                    name="lifecycle_manager",
                    namespace=name,
                    output="screen",
                    parameters=[{**common, "autostart": True, "node_names": ["map_server", "amcl"]}],
                )]),
            ]
        )
        actions.append(TimerAction(period=3.0 * index, actions=case_actions))
    return actions


def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument("cases_file"), OpaqueFunction(function=launch_cases)])
