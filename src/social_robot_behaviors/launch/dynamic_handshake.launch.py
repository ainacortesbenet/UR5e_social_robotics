import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    perception_dir = get_package_share_directory("social_robot_perception")
    hri_dir = get_package_share_directory("social_robot_hri")
    behaviors_dir = get_package_share_directory("social_robot_behaviors")

    execute = LaunchConfiguration("execute")

    return LaunchDescription([
        DeclareLaunchArgument(
            "execute",
            default_value="false",
            description="Plan only when false; command the robot when true.",
        ),
        Node(
            package="social_robot_perception",
            executable="pose_3d_node",
            name="pose_3d_node",
            output="screen",
            parameters=[os.path.join(
                perception_dir, "config", "pose_3d_params.yaml"
            )],
        ),
        Node(
            package="social_robot_hri",
            executable="gesture_interpreter_node",
            name="gesture_interpreter_node",
            output="screen",
            parameters=[os.path.join(
                hri_dir, "config", "gesture_interpreter_params.yaml"
            )],
        ),
        Node(
            package="social_robot_behaviors",
            executable="interaction_manager_node",
            name="interaction_manager_node",
            output="screen",
            parameters=[
                os.path.join(
                    behaviors_dir, "config", "interaction_manager_params.yaml"
                ),
                {"execute": ParameterValue(execute, value_type=bool)},
            ],
        ),
    ])
