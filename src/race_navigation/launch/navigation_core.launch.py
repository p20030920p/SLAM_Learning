"""Minimal Nav2 stack: controller, planner, behaviours, BT navigator.

The upstream Jazzy navigation launch also starts route planning and docking.
Those servers are unrelated to this workspace, docking can delay lifecycle
startup, and none of them have parameters configured here, so this launch
intentionally manages only the nodes the task needs.

Velocity chain, end to end:

    controller_server -> /nav2_controller/cmd_vel_raw
    velocity_smoother -> /nav2_controller/cmd_vel_smoothed
    collision_monitor -> /cmd_vel
    twist_to_twist_stamped (race_bringup) -> /omni_drive_controller/cmd_vel

/cmd_vel is also the topic the keyboard teleop publishes to, so driving by hand
and driving by Nav2 use the same entry point into the robot — just not at the
same time.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, SetParameter
from launch_ros.descriptions import ParameterFile
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')
    params_file = LaunchConfiguration('params_file')

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key='',
            param_rewrites={'autostart': autostart},
            convert_types=True,
        ),
        allow_substs=True,
    )

    tf_remaps = [('/tf', 'tf'), ('/tf_static', 'tf_static')]
    lifecycle_nodes = [
        'controller_server',
        'smoother_server',
        'planner_server',
        'behavior_server',
        'velocity_smoother',
        'collision_monitor',
        'bt_navigator',
    ]

    nodes = GroupAction(actions=[
        SetParameter('use_sim_time', use_sim_time),
        Node(
            package='nav2_controller', executable='controller_server',
            name='controller_server', output='screen',
            parameters=[configured_params],
            remappings=tf_remaps + [('cmd_vel', '/nav2_controller/cmd_vel_raw')],
        ),
        Node(
            package='nav2_smoother', executable='smoother_server',
            name='smoother_server', output='screen',
            parameters=[configured_params], remappings=tf_remaps,
        ),
        Node(
            package='nav2_planner', executable='planner_server',
            name='planner_server', output='screen',
            parameters=[configured_params], remappings=tf_remaps,
        ),
        Node(
            package='nav2_behaviors', executable='behavior_server',
            name='behavior_server', output='screen',
            parameters=[configured_params],
            remappings=tf_remaps + [('cmd_vel', '/nav2_controller/cmd_vel_raw')],
        ),
        Node(
            package='nav2_bt_navigator', executable='bt_navigator',
            name='bt_navigator', output='screen',
            parameters=[configured_params], remappings=tf_remaps,
        ),
        Node(
            package='nav2_velocity_smoother', executable='velocity_smoother',
            name='velocity_smoother', output='screen',
            parameters=[configured_params],
            remappings=tf_remaps + [
                ('cmd_vel', '/nav2_controller/cmd_vel_raw'),
                ('cmd_vel_smoothed', '/nav2_controller/cmd_vel_smoothed'),
            ],
        ),
        Node(
            package='nav2_collision_monitor', executable='collision_monitor',
            name='collision_monitor', output='screen',
            parameters=[configured_params],
            # cmd_vel_out_topic is "cmd_vel" in the parameters, so the collision
            # monitor's output lands on /cmd_vel and feeds the simulation's
            # Twist -> TwistStamped adapter. Only the input side needs remapping.
            remappings=tf_remaps + [
                ('cmd_vel_smoothed', '/nav2_controller/cmd_vel_smoothed'),
            ],
        ),
        Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_navigation', output='screen',
            parameters=[{'autostart': autostart, 'node_names': lifecycle_nodes}],
        ),
    ])

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('autostart', default_value='true'),
        DeclareLaunchArgument('params_file'),
        nodes,
    ])
