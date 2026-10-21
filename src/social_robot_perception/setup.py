from glob import glob
import os

from setuptools import setup


package_name = "social_robot_perception"


setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Manel Puig",
    maintainer_email="puigmanel@gmail.com",
    description="3D human-pose perception using an RGB-D camera and YOLO Pose",
    license="MIT",
    entry_points={
        "console_scripts": [
            "pose_3d_node = social_robot_perception.pose_3d_node:main",
        ],
    },
)
