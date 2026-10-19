#!/usr/bin/env python3

import os
import re
import subprocess

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from ur5e_interfaces.srv import RunSequence


class UR5eSequenceServer(Node):

    def __init__(self):

        super().__init__("ur5e_sequence_server")

        package_share_dir = get_package_share_directory(
            "social_robot_behaviors"
        )

        default_sequences_dir = os.path.join(
            package_share_dir,
            "motions"
        )

        self.declare_parameter(
            "sequences_dir",
            default_sequences_dir
        )

        self.declare_parameter(
            "service_name",
            "/ur5e/run_sequence"
        )

        self.sequences_dir = os.path.abspath(
            self.get_parameter("sequences_dir").value
        )

        self.service_name = self.get_parameter(
            "service_name"
        ).value

        self.busy = False

        self.srv = self.create_service(
            RunSequence,
            self.service_name,
            self.run_sequence_callback
        )

        self.get_logger().info(
            "UR5e sequence server ready."
        )

        self.get_logger().info(
            f"Service: {self.service_name}"
        )

        self.get_logger().info(
            f"Sequences directory: {self.sequences_dir}"
        )

    # =============================================================
    # Validate and resolve sequence file
    # =============================================================

    def resolve_sequence_file(
        self,
        sequence_name: str
    ) -> str | None:

        sequence_name = sequence_name.strip()

        # Accept both "give5" and "give5.yaml"
        if sequence_name.endswith(".yaml"):
            sequence_name = sequence_name[:-5]

        # Allow names such as:
        # give5, hand_shake, my-social-motion
        if not re.fullmatch(
            r"[A-Za-z0-9_-]+",
            sequence_name
        ):
            return None

        filename = f"{sequence_name}.yaml"

        sequence_file = os.path.abspath(
            os.path.join(
                self.sequences_dir,
                filename
            )
        )

        # Protection against path traversal
        if os.path.commonpath(
            [self.sequences_dir, sequence_file]
        ) != self.sequences_dir:
            return None

        return sequence_file

    # =============================================================
    # Service callback
    # =============================================================

    def run_sequence_callback(
        self,
        request,
        response
    ):

        if self.busy:

            response.success = False
            response.message = "Robot busy."

            return response

        sequence_name = request.sequence_name.strip()

        sequence_file = self.resolve_sequence_file(
            sequence_name
        )

        if sequence_file is None:

            response.success = False
            response.message = (
                f"Invalid sequence name: '{sequence_name}'"
            )

            return response

        if not os.path.isfile(sequence_file):

            response.success = False
            response.message = (
                f"Sequence not found: "
                f"{os.path.basename(sequence_file)}"
            )

            self.get_logger().error(
                f"Sequence file not found: {sequence_file}"
            )

            return response

        self.get_logger().info(
            f"Executing sequence: {sequence_name}"
        )

        self.get_logger().info(
            f"Sequence file: {sequence_file}"
        )

        self.busy = True

        try:

            cmd = [
                "ros2",
                "launch",
                "ur5e_robot_controller",
                "ur5e_pose_sequence.launch.py",
                f"sequence_file:={os.path.basename(sequence_file)}",
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.stdout:

                self.get_logger().info(
                    result.stdout
                )

            if result.returncode != 0:

                if result.stderr:

                    self.get_logger().error(
                        result.stderr
                    )

                response.success = False
                response.message = (
                    f"Sequence '{sequence_name}' failed."
                )

            else:

                response.success = True
                response.message = (
                    f"Sequence '{sequence_name}' executed."
                )

        except Exception as exc:

            self.get_logger().error(
                f"Sequence execution exception: {exc}"
            )

            response.success = False
            response.message = (
                f"Execution error: {exc}"
            )

        finally:

            self.busy = False

        return response


def main(args=None):

    rclpy.init(args=args)

    node = UR5eSequenceServer()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
