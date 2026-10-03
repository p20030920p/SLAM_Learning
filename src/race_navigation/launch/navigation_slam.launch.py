"""SLAM + navigation at the same time: slam_toolbox builds the map while Nav2
plans on it.

Use this to drive around an unknown arena and watch the map grow. AMCL is *not*
started here on purpose: slam_toolbox owns the map -> odom transform, and AMCL
would fight it for the same edge of the TF tree. Once the map is saved, switch
to localization_navigation.launch.py, which runs AMCL against the saved map.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # The simulation launch always forces its own inner rviz to false (see
    # sim_ros2_control.launch.py); 'rviz' below only controls this outer one, so
    # the two are deliberately kept separate.
    sim_launch = PathJoinSubstitution([
        FindPackageShare('race_bringup'),
        'launch',
        'sim_ros2_control.launch.py',
    ])
    slam_launch = PathJoinSubstitution([FindPackageShare('nav2_bringup'), 'launch', 'slam_launch.py'])
    nav_launch = PathJoinSubstitution([
        FindPackageShare('race_navigation'), 'launch', 'navigation_core.launch.py'])
    slam_params = PathJoinSubstitution([FindPackageShare('race_navigation'), 'config', 'slam_toolbox.yaml'])
    nav_params = PathJoinSubstitution([FindPackageShare('race_navigation'), 'config', 'nav2_params.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                'headless': LaunchConfiguration('headless'),
                'paused': 'false',
                'rviz': LaunchConfiguration('rviz'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        ),
        # slam_toolbox first: Nav2's global costmap needs a publisher on /map.
        TimerAction(
            period=12.0,
            actions=[IncludeLaunchDescription(
                PythonLaunchDescriptionSource(slam_launch),
                launch_arguments={
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'params_file': slam_params,
                }.items(),
            )],
        ),
        TimerAction(
            period=16.0,
            actions=[IncludeLaunchDescription(
                PythonLaunchDescriptionSource(nav_launch),
                launch_arguments={
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                    'params_file': nav_params,
                    'autostart': LaunchConfiguration('autostart'),
                }.items(),
            )],
        ),
    ])
