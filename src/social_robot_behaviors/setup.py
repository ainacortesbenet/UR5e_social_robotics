from setuptools import setup
from glob import glob
import os

package_name = "social_robot_behaviors"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],

    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        (
            "share/" + package_name,
            ["package.xml"],
        ),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
        (
            os.path.join("share", package_name, "motions"),
            glob("motions/*.yaml"),
        ),
    ],

    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Manel Puig",
    maintainer_email="puigmanel@gmail.com",
    description="Social robot behavior manager",
    license="Apache-2.0",

    entry_points={
        "console_scripts": [
            "behavior_manager_client_node = social_robot_behaviors.behavior_manager_client_node:main",
            "interaction_manager_node = social_robot_behaviors.interaction_manager_node:main",
            'ur5e_pose_client = social_robot_behaviors.ur5e_pose_client:main',
            'ur5e_fkine_client = social_robot_behaviors.ur5e_fkine_client:main',
        ],
    },
)
