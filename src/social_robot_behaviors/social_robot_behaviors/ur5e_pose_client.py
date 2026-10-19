#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from ur5e_interfaces.srv import RunPose


class UR5ePoseClient(Node):

    def __init__(self):
        super().__init__("ur5e_pose_client")

        self.declare_parameter("service_name", "/ur5e/run_pose")
        self.declare_parameter("target_xyz", [0.0, -400.0, 500.0])
        self.declare_parameter("target_rpy", [90.0, 0.0, 0.0])
        self.declare_parameter("seed_from_joint_states", True)
        self.declare_parameter("seed_joints", [-60.0, -60.0, -100.0, 170.0, -60.0, 0.0])
        self.declare_parameter("execute", True)

        service_name = self.get_parameter("service_name").value

        self.client = self.create_client(RunPose, service_name)

    def call_server(self):
        service_name = self.get_parameter("service_name").value

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f"Waiting for service {service_name}...")

        req = RunPose.Request()

        req.target_xyz_mm = [
            float(v) for v in self.get_parameter("target_xyz").value
        ]

        req.target_rpy_deg = [
            float(v) for v in self.get_parameter("target_rpy").value
        ]

        req.seed_from_joint_states = bool(
            self.get_parameter("seed_from_joint_states").value
        )

        req.seed_joints_deg = [
            float(v) for v in self.get_parameter("seed_joints").value
        ]

        req.execute = bool(
            self.get_parameter("execute").value
        )

        self.get_logger().info(f"target_xyz_mm: {req.target_xyz_mm}")
        self.get_logger().info(f"target_rpy_deg: {req.target_rpy_deg}")
        self.get_logger().info(f"seed_from_joint_states: {req.seed_from_joint_states}")
        self.get_logger().info(f"seed_joints_deg: {req.seed_joints_deg}")
        self.get_logger().info(f"execute: {req.execute}")

        future = self.client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        response = future.result()

        if response is None:
            self.get_logger().error("Service call failed.")
            return

        self.get_logger().info(f"success: {response.success}")
        self.get_logger().info(f"message: {response.message}")


def main(args=None):
    rclpy.init(args=args)

    node = UR5ePoseClient()
    node.call_server()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
