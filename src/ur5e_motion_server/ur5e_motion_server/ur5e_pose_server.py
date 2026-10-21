#!/usr/bin/env python3

import subprocess

import rclpy
from rclpy.node import Node

from ur5e_interfaces.srv import RunPose


class UR5ePoseServer(Node):

    def __init__(self):
        super().__init__("ur5e_pose_server")

        self.declare_parameter("launch_package", "ur5e_robot_controller")
        self.declare_parameter("launch_file", "ur5e_pose.launch.py")

        self.launch_package = self.get_parameter("launch_package").value
        self.launch_file = self.get_parameter("launch_file").value
        self.busy = False

        self.srv = self.create_service(
            RunPose,
            "/ur5e/run_pose",
            self.run_pose_callback,
        )

        self.get_logger().info("UR5e pose server ready.")
        self.get_logger().info("Service: /ur5e/run_pose")
        self.get_logger().info(
            f"Launch target: {self.launch_package} {self.launch_file}"
        )

    def run_pose_callback(self, request, response):

        if self.busy:
            response.success = False
            response.message = "Robot busy."
            return response

        self.busy = True

        try:
            target_xyz = [float(v) for v in request.target_xyz_mm]
            target_rpy = [float(v) for v in request.target_rpy_deg]
            seed_joints = [float(v) for v in request.seed_joints_deg]

            cmd = [
                "ros2",
                "launch",
                self.launch_package,
                self.launch_file,

                f"target_xyz:={target_xyz}",
                f"target_rpy:={target_rpy}",
                f"seed_from_joint_states:={str(request.seed_from_joint_states).lower()}",
                f"seed_joints:={seed_joints}",
                f"execute:={str(request.execute).lower()}",
                f"max_velocity:={float(request.max_velocity)}",
                f"max_acceleration:={float(request.max_acceleration)}",
            ]

            self.get_logger().info("Executing pose using launch command:")
            self.get_logger().info(" ".join(cmd))

            result = subprocess.run(cmd, check=False)

            response.success = result.returncode == 0
            response.message = (
                "Pose execution completed."
                if response.success
                else f"Pose launch failed with code {result.returncode}."
            )

        except Exception as e:
            response.success = False
            response.message = f"Exception: {e}"

        finally:
            self.busy = False

        return response


def main():

    rclpy.init()

    node = UR5ePoseServer()

    rclpy.spin(node)

    rclpy.shutdown()


if __name__ == "__main__":
    main()
