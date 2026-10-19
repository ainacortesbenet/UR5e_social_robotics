#!/usr/bin/env python3

from functools import partial

import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import PoseStamped
from rclpy.duration import Duration
from rclpy.node import Node
from std_msgs.msg import String
from tf2_ros import Buffer, TransformException, TransformListener
import tf2_geometry_msgs  # noqa: F401 - registers PoseStamped conversions

from ur5e_interfaces.srv import RunPose


class InteractionManagerNode(Node):
    """Coordinate the first camera-driven dynamic handshake."""

    def __init__(self):
        super().__init__("interaction_manager_node")

        self.declare_parameter("intent_topic", "/social_intent")
        self.declare_parameter("wrist_topic", "/wrist_pose")
        self.declare_parameter("pose_service", "/ur5e/run_pose")
        self.declare_parameter("target_frame", "table")
        self.declare_parameter("maximum_pose_age_sec", 0.5)
        self.declare_parameter("step_interval_sec", 1.0)
        self.declare_parameter("approach_offset_z_mm", 100.0)
        self.declare_parameter("shake_amplitude_z_mm", 30.0)
        self.declare_parameter("target_rpy_deg", [90.0, 0.0, 0.0])
        self.declare_parameter("home_xyz_mm", [0.0, -400.0, 500.0])
        self.declare_parameter(
            "home_seed_joints_deg",
            [-60.0, -60.0, -100.0, 170.0, -60.0, 0.0],
        )
        self.declare_parameter(
            "workspace_min_mm", [-600.0, -700.0, 50.0]
        )
        self.declare_parameter("workspace_max_mm", [600.0, 100.0, 700.0])
        self.declare_parameter("execute", False)
        self.declare_parameter("max_velocity", 0.05)
        self.declare_parameter("max_acceleration", 0.05)

        self.latest_wrist_pose = None
        self.latest_wrist_receive_time = None
        self.busy = False
        self.pending_steps = []
        self.step_timer = None

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.pose_client = self.create_client(
            RunPose, self.get_parameter("pose_service").value
        )

        self.create_subscription(
            PoseStamped,
            self.get_parameter("wrist_topic").value,
            self.wrist_callback,
            10,
        )
        self.create_subscription(
            String,
            self.get_parameter("intent_topic").value,
            self.intent_callback,
            10,
        )

        self.get_logger().info(
            "Interaction manager started. execute=%s"
            % self.get_parameter("execute").value
        )

    def wrist_callback(self, msg: PoseStamped):
        self.latest_wrist_pose = msg
        self.latest_wrist_receive_time = self.get_clock().now()

    def wrist_pose_is_recent(self) -> bool:
        if self.latest_wrist_receive_time is None:
            return False
        age = (
            self.get_clock().now() - self.latest_wrist_receive_time
        ).nanoseconds / 1e9
        return age <= float(
            self.get_parameter("maximum_pose_age_sec").value
        )

    def transform_wrist_to_target(self):
        pose = PoseStamped()
        pose.header = self.latest_wrist_pose.header
        pose.pose = self.latest_wrist_pose.pose

        # The newest calibrated transform is preferable to extrapolation errors.
        pose.header.stamp = Time()
        target_frame = self.get_parameter("target_frame").value
        try:
            return self.tf_buffer.transform(
                pose,
                target_frame,
                timeout=Duration(seconds=0.2),
            )
        except TransformException as exc:
            self.get_logger().error(
                f"Cannot transform wrist pose to {target_frame}: {exc}"
            )
            return None

    def inside_workspace(self, xyz_mm) -> bool:
        minimum = self.get_parameter("workspace_min_mm").value
        maximum = self.get_parameter("workspace_max_mm").value
        return all(
            float(minimum[index]) <= xyz_mm[index] <= float(maximum[index])
            for index in range(3)
        )

    def intent_callback(self, msg: String):
        if msg.data.strip() != "handshake_offer":
            return
        if self.busy:
            self.get_logger().warning(
                "Ignoring handshake offer: manager is busy."
            )
            return
        if not self.wrist_pose_is_recent():
            self.get_logger().warning(
                "Ignoring handshake offer: wrist pose is missing or old."
            )
            return
        if not self.pose_client.service_is_ready():
            self.get_logger().error("The /ur5e/run_pose service is not ready.")
            return

        target_pose = self.transform_wrist_to_target()
        if target_pose is None:
            return

        target = [
            1000.0 * target_pose.pose.position.x,
            1000.0 * target_pose.pose.position.y,
            1000.0 * target_pose.pose.position.z,
        ]
        if not self.inside_workspace(target):
            self.get_logger().warning(
                f"Ignoring unsafe or unreachable wrist target [mm]: {target}"
            )
            return

        approach_offset = float(
            self.get_parameter("approach_offset_z_mm").value
        )
        shake_amplitude = float(
            self.get_parameter("shake_amplitude_z_mm").value
        )
        approach = [target[0], target[1], target[2] + approach_offset]
        shake_up = [target[0], target[1], target[2] + shake_amplitude]
        shake_down = [target[0], target[1], target[2] - shake_amplitude]
        home = [float(v) for v in self.get_parameter("home_xyz_mm").value]

        steps = [
            ("approach", approach, True),
            ("contact", target, True),
            ("shake_up", shake_up, True),
            ("shake_down", shake_down, True),
            ("shake_up", shake_up, True),
            ("retreat", approach, True),
            ("home", home, False),
        ]
        unsafe_steps = [
            name for name, xyz, _ in steps
            if not self.inside_workspace(xyz)
        ]
        if unsafe_steps:
            self.get_logger().warning(
                "Handshake rejected: steps outside the workspace: "
                f"{unsafe_steps}"
            )
            return

        self.pending_steps = steps
        self.busy = True
        self.get_logger().info(
            f"Starting handshake_dynamic at wrist target [mm]: {target}"
        )
        self.run_next_step()

    def run_next_step(self):
        if not self.pending_steps:
            self.busy = False
            self.get_logger().info("handshake_dynamic completed.")
            return

        name, xyz_mm, seed_from_joint_states = self.pending_steps.pop(0)
        request = RunPose.Request()
        request.target_xyz_mm = xyz_mm
        request.target_rpy_deg = [
            float(v) for v in self.get_parameter("target_rpy_deg").value
        ]
        request.seed_from_joint_states = seed_from_joint_states
        request.seed_joints_deg = [
            float(v)
            for v in self.get_parameter("home_seed_joints_deg").value
        ]
        request.execute = bool(self.get_parameter("execute").value)
        request.max_velocity = float(self.get_parameter("max_velocity").value)
        request.max_acceleration = float(
            self.get_parameter("max_acceleration").value
        )

        self.get_logger().info(f"Requesting step '{name}': {xyz_mm} mm")
        future = self.pose_client.call_async(request)
        future.add_done_callback(partial(self.step_response, name=name))

    def step_response(self, future, name):
        try:
            response = future.result()
        except Exception as exc:
            self.abort_handshake(f"Step '{name}' service failure: {exc}")
            return

        if not response.success:
            self.abort_handshake(f"Step '{name}' rejected: {response.message}")
            return

        delay = float(self.get_parameter("step_interval_sec").value)
        self.step_timer = self.create_timer(delay, self.step_timer_callback)

    def step_timer_callback(self):
        self.step_timer.cancel()
        self.destroy_timer(self.step_timer)
        self.step_timer = None
        self.run_next_step()

    def abort_handshake(self, reason: str):
        self.pending_steps = []
        self.busy = False
        self.get_logger().error(reason)


def main(args=None):
    rclpy.init(args=args)
    node = InteractionManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
