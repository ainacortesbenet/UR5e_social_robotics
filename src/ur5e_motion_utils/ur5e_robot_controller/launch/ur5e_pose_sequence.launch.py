from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    TimerAction,
    RegisterEventHandler,
    EmitEvent,
)
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    sequence_file = LaunchConfiguration("sequence_file")

    sequence_path = PathJoinSubstitution([
        FindPackageShare("social_robot_behaviors"),
        "motions",
        sequence_file,
    ])

    sequence_arg = DeclareLaunchArgument(
        "sequence_file",
        default_value="handshake.yaml",
        description="YAML filename installed by social_robot_behaviors",
    )

    static_table_tf = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_base_link_to_table",
        output="screen",
        arguments=[
            "0.0", "0.0", "0.0",
            "0.0", "0.0", "1.0", "0.0",
            "base_link",
            "table",
        ],
    )

    sequence_node = Node(
        package="ur5e_robot_controller",
        executable="ur5e_pose_sequence_exe",
        name="ur5e_pose_sequence",
        output="screen",
        parameters=[{
            "sequence_file": sequence_path,
        }],
    )

    delayed_sequence_node = TimerAction(
        period=2.0,
        actions=[sequence_node],
    )

    shutdown_on_sequence_exit = RegisterEventHandler(
        OnProcessExit(
            target_action=sequence_node,
            on_exit=[
                EmitEvent(
                    event=Shutdown(
                        reason="UR5e pose sequence finished"
                    )
                )
            ],
        )
    )

    return LaunchDescription([
        sequence_arg,
        static_table_tf,
        delayed_sequence_node,
        shutdown_on_sequence_exit,
    ])
