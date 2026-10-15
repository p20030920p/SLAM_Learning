"""Identical FAST-LIO2 parameters and inputs; only point correction is ablated."""
from pathlib import Path
import json
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def launch_nodes(context):
    run = Path(LaunchConfiguration("run").perform(context))
    return [Node(package="fast_lio", executable="fastlio_mapping", name="mapping", namespace=name,
                 parameters=[str(run / "fastlio.yaml")], output="screen",
                 additional_env={"FASTLIO_STUDY_NO_DESKEW":"1"} if name == "no_deskew" else {},
                 remappings=[("/"+topic,f"/{name}/{topic}") for topic in
                             ("tf","tf_static","cloud_registered","cloud_registered_body","cloud_effected","Laser_map","Odometry","path")])
            for name in ("deskew","no_deskew")]

def generate_launch_description():
    return LaunchDescription([DeclareLaunchArgument("run"), OpaqueFunction(function=launch_nodes)])
