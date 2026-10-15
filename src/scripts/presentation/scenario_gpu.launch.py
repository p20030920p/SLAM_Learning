# GPU presentation adapter; based on the locally prepared Sim2Real scenario launcher.
# Source path/hash is retained in each session. Native chassis/control remain upstream.
#!/usr/bin/env python3
"""One launcher for all four scenario levels, headless.

This file is deliberately self-contained: it never edits the upstream launch
files, so `ros2 launch race_navigation competition.launch.py ...` keeps behaving
exactly as the repository ships it.  What it reuses from the repository is the
robot (URDF), the ros2_control configuration, the sensor bridge configuration
and the SLAM parameters.

Everything it starts, and the arguments that select it:

    Gazebo (server only by default) with `world`
    robot_state_publisher from `urdf`
    ros_gz_bridge with `bridge_config`
    ros_gz_sim create  -> spawns the robot at spawn_{x,y,z,yaw}
    controller spawners: joint_state_broadcaster, omni_drive_controller
    twist_to_twist_stamped: /cmd_vel (Twist) -> /omni_drive_controller/cmd_vel
    `obstacles` moving obstacles (0, 2 or 3) with their command bridges
    `slam:=true`   -> slam_toolbox mapping, publishes /map
    `patrol:=true` -> waypoint driver, see race_nodes/patrol_waypoints.py
    `truth:=true`  -> bridge the simulator's true model poses to ROS

Usage:
    ros2 launch scenario_variants/launch/scenario.launch.py \
        world:=<abs path>.world urdf:=<abs path>.urdf slam:=true patrol:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

REPO = os.environ.get("S2R_REPO", "/root/projects/Sim2Real-AlgoBench")
VARIANTS = os.path.normpath(os.path.join(os.path.dirname(__file__), "../../../config/presentation"))
RACE_NODES = os.path.dirname(__file__)
DEFAULT_WORLD = os.path.join(VARIANTS, "worlds", "S1_static.world")

# Obstacle command topics.  Index 0 and 1 are the two the repository ships, the
# third exists only in S2_dynamic.world.
OBSTACLE_TOPICS = ["/dynamic_obstacle/cmd_pos", "/dynamic_obstacle_2/cmd_pos", "/dynamic_obstacle_3/cmd_pos"]
OBSTACLE_AMPLITUDES = [1.6, 1.4, 1.75]
OBSTACLE_PERIODS = [8.0, 7.0, 6.0]


def _start_gazebo(context, *_args, **_kwargs):
    """Launch the Gazebo server with the selected world and resource paths."""
    pkg_share = get_package_share_directory("race_gazebo")
    models_dir = os.path.join(pkg_share, "models")
    desc_share = get_package_share_directory("race_description")
    desc_root = os.path.dirname(desc_share)

    world = LaunchConfiguration("world").perform(context)
    headless = LaunchConfiguration("headless").perform(context).lower() in ("1", "true", "yes", "on")
    render_engine = LaunchConfiguration("render_engine").perform(context)

    gz_args = []
    if headless:
        gz_args += ["-s", "--headless-rendering"]
    gz_args += ["-r", "--render-engine", render_engine, world]
    gui_config = os.environ.get("PRESENTATION_GUI_CONFIG")
    if gui_config:
        gz_args += ["--gui-config", gui_config]

    gz_launch = PathJoinSubstitution([FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"])
    return [
        AppendEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=models_dir),
        AppendEnvironmentVariable(name="GZ_SIM_RESOURCE_PATH", value=desc_root),
        # gz_ros2_control's system plugin lives in the ROS lib directory; the
        # repository's own recording script exports the same variable.
        AppendEnvironmentVariable(name="GZ_SIM_SYSTEM_PLUGIN_PATH", value="/opt/ros/jazzy/lib"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch), launch_arguments={"gz_args": " ".join(gz_args)}.items()
        ),
    ]


def generate_launch_description():
    race_bringup_share = FindPackageShare("race_bringup")
    race_desc_share = FindPackageShare("race_description")

    urdf_default = PathJoinSubstitution([race_desc_share, "urdf", "omni_car_ros2_control.urdf"])
    bridge_default = PathJoinSubstitution([race_bringup_share, "config", "bridge_sensors.yaml"])
    slam_params = PathJoinSubstitution([FindPackageShare("race_navigation"), "config", "slam_toolbox.yaml"])
    nav2_params = PathJoinSubstitution([FindPackageShare("race_navigation"), "config", "nav2_params.yaml"])
    slam_launch = PathJoinSubstitution([FindPackageShare("nav2_bringup"), "launch", "slam_launch.py"])
    localization_launch = PathJoinSubstitution(
        [FindPackageShare("nav2_bringup"), "launch", "localization_launch.py"]
    )

    patrol_waypoints = LaunchConfiguration("waypoints")

    robot_description = ParameterValue(Command(["xacro ", LaunchConfiguration("urdf")]), value_type=str)

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"robot_description": robot_description, "use_sim_time": LaunchConfiguration("use_sim_time")}
        ],
    )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_sensor_bridge",
        output="screen",
        parameters=[{"config_file": LaunchConfiguration("bridge_config")}],
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_omni_car",
        output="screen",
        arguments=[
            "-name",
            "omni_car",
            "-topic",
            "robot_description",
            "-x",
            LaunchConfiguration("spawn_x"),
            "-y",
            LaunchConfiguration("spawn_y"),
            "-z",
            LaunchConfiguration("spawn_z"),
            "-Y",
            LaunchConfiguration("spawn_yaw"),
        ],
    )

    joint_state_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    omni_spawner = Node(
        package="controller_manager",
        executable="spawner",
        output="screen",
        arguments=["omni_drive_controller", "--controller-manager", "/controller_manager"],
    )

    cmd_vel_converter = Node(
        package="race_control",
        executable="twist_to_twist_stamped",
        name="twist_to_twist_stamped",
        output="screen",
        parameters=[
            {
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "in_topic": "/cmd_vel",
                "out_topic": "/omni_drive_controller/cmd_vel",
                "frame_id": "base_footprint",
            }
        ],
    )

    # ---- moving obstacles -------------------------------------------------
    obstacle_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_moving_obstacle_bridge",
        output="screen",
        arguments=[f"{t}@std_msgs/msg/Float64]gz.msgs.Double" for t in OBSTACLE_TOPICS],
        condition=IfCondition(LaunchConfiguration("obstacles")),
    )

    obstacle_nodes = [
        Node(
            package="race_control",
            executable="moving_obstacle",
            name=f"moving_obstacle_{i + 1}",
            output="screen",
            parameters=[
                {
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "command_topic": topic,
                    "amplitude": amp,
                    "period_seconds": period,
                }
            ],
        )
        for i, (topic, amp, period) in enumerate(zip(OBSTACLE_TOPICS, OBSTACLE_AMPLITUDES, OBSTACLE_PERIODS))
    ]

    # ---- true model poses -------------------------------------------------
    truth_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_truth_bridge",
        output="screen",
        arguments=["/world/competition_world/dynamic_pose/info" "@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V"],
        condition=IfCondition(LaunchConfiguration("truth")),
    )

    # ---- SLAM -------------------------------------------------------------
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_launch),
        launch_arguments={
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file": slam_params,
        }.items(),
    )

    # ---- localization against a prior map ---------------------------------
    # This is what makes S3 a *large change* and not merely a different arena:
    # the map was built in S1 and saved, and the robot is then localized in the
    # modified world against that stale map.
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(localization_launch),
        launch_arguments={
            "map": LaunchConfiguration("map"),
            "use_sim_time": LaunchConfiguration("use_sim_time"),
            "params_file": nav2_params,
            "autostart": "true",
            "use_composition": "False",
            "use_respawn": "False",
        }.items(),
    )

    # ---- waypoint driver --------------------------------------------------
    # The patrol node steers on wheel odometry, which starts at (0,0,0) wherever
    # the robot was spawned, so the spawn pose is handed to it as the origin.
    patrol = ExecuteProcess(
        cmd=[
            "python3",
            os.path.join(RACE_NODES, "patrol_waypoints.py"),
            "--ros-args",
            "-p",
            ["waypoints:=", patrol_waypoints],
            "-p",
            ["speed:=", LaunchConfiguration("patrol_speed")],
            "-p",
            ["hold:=", LaunchConfiguration("patrol_hold")],
            "-p",
            ["use_sim_time:=", LaunchConfiguration("use_sim_time")],
            "-p",
            ["origin_x:=", LaunchConfiguration("spawn_x")],
            "-p",
            ["origin_y:=", LaunchConfiguration("spawn_y")],
            "-p",
            ["origin_yaw:=", LaunchConfiguration("spawn_yaw")],
        ],
        name="patrol_waypoints",
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world", default_value=DEFAULT_WORLD, description="Absolute path of the .world to load."
            ),
            DeclareLaunchArgument(
                "urdf", default_value=urdf_default, description="Robot description to spawn."
            ),
            DeclareLaunchArgument(
                "bridge_config", default_value=bridge_default, description="ros_gz_bridge sensor config YAML."
            ),
            DeclareLaunchArgument("headless", default_value="true"),
            DeclareLaunchArgument("render_engine", default_value="ogre2"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument(
                "obstacles",
                default_value="false",
                description="Start the moving obstacles (the S2 " "world contains three of them).",
            ),
            DeclareLaunchArgument("slam", default_value="false"),
            DeclareLaunchArgument(
                "localize",
                default_value="false",
                description="AMCL + map_server against `map` " "(used by S3: S1-built map, S3 world).",
            ),
            DeclareLaunchArgument(
                "map",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("race_navigation"), "maps", "race_map.yaml"]
                ),
                description="Prior map for localize:=true.",
            ),
            DeclareLaunchArgument("patrol", default_value="false"),
            DeclareLaunchArgument("patrol_speed", default_value="0.35"),
            DeclareLaunchArgument("patrol_hold", default_value="3.0"),
            DeclareLaunchArgument("truth", default_value="false"),
            DeclareLaunchArgument("waypoints", default_value="8.5,7.6;5.3,7.6"),
            DeclareLaunchArgument("spawn_x", default_value="8.0727"),
            DeclareLaunchArgument("spawn_y", default_value="7.5312"),
            DeclareLaunchArgument("spawn_z", default_value="0.25"),
            DeclareLaunchArgument("spawn_yaw", default_value="-1.5708"),
            OpaqueFunction(function=_start_gazebo),
            robot_state_publisher,
            gz_bridge,
            truth_bridge,
            obstacle_bridge,
            TimerAction(period=3.0, actions=[spawn_robot]),
            TimerAction(period=7.0, actions=[joint_state_spawner]),
            TimerAction(period=9.0, actions=[omni_spawner]),
            TimerAction(period=10.0, actions=[cmd_vel_converter]),
            TimerAction(
                period=13.0, condition=IfCondition(LaunchConfiguration("obstacles")), actions=obstacle_nodes
            ),
            TimerAction(period=12.0, condition=IfCondition(LaunchConfiguration("slam")), actions=[slam]),
            TimerAction(
                period=12.0, condition=IfCondition(LaunchConfiguration("localize")), actions=[localization]
            ),
            TimerAction(period=22.0, condition=IfCondition(LaunchConfiguration("patrol")), actions=[patrol]),
        ]
    )
