import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory("social_robot_hri")
    params_file = os.path.join(
        package_dir, "config", "gesture_interpreter_params.yaml"
    )

    return LaunchDescription([
        Node(
            package="social_robot_hri",
            executable="gesture_interpreter_node",
            name="gesture_interpreter_node",
            output="screen",
            parameters=[params_file],
        ),
    ])
