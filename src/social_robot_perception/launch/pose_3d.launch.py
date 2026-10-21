import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory("social_robot_perception")
    params_file = os.path.join(package_dir, "config", "pose_3d_params.yaml")

    return LaunchDescription([
        Node(
            package="social_robot_perception",
            executable="pose_3d_node",
            name="pose_3d_node",
            output="screen",
            parameters=[params_file],
        ),
    ])
