#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import PoseArray
from rclpy.node import Node
from std_msgs.msg import String


LEFT_SHOULDER = 5
RIGHT_SHOULDER = 6
LEFT_ELBOW = 7
RIGHT_ELBOW = 8
LEFT_WRIST = 9
RIGHT_WRIST = 10


class GestureInterpreterNode(Node):

    def __init__(self):
        super().__init__('gesture_interpreter_node')

        self.declare_parameter("input_topic", "/person_pose_3d")
        self.declare_parameter("output_topic", "/social_intent")
        self.declare_parameter("wrist_side", "right")
        self.declare_parameter("minimum_arm_extension_m", 0.30)
        self.declare_parameter("minimum_forward_reach_m", 0.10)
        self.declare_parameter("required_frames", 8)
        self.declare_parameter("cooldown_sec", 5.0)

        self.matching_frames = 0
        self.last_detection_time = None

        self.intent_publisher = self.create_publisher(
            String,
            self.get_parameter("output_topic").value,
            10,
        )
        self.create_subscription(
            PoseArray,
            self.get_parameter("input_topic").value,
            self.pose_callback,
            10,
        )

        self.get_logger().info(
            "Gesture interpreter started. Waiting for a handshake offer."
        )

    @staticmethod
    def point_is_valid(pose) -> bool:
        return all(
            math.isfinite(value)
            for value in (
                pose.position.x,
                pose.position.y,
                pose.position.z,
            )
        )

    @staticmethod
    def distance(first, second) -> float:
        return math.sqrt(
            (first.position.x - second.position.x) ** 2
            + (first.position.y - second.position.y) ** 2
            + (first.position.z - second.position.z) ** 2
        )

    def pose_callback(self, msg: PoseArray):
        if len(msg.poses) < 17:
            return

        side = str(self.get_parameter("wrist_side").value).lower()
        if side == "left":
            shoulder_index, elbow_index, wrist_index = (
                LEFT_SHOULDER,
                LEFT_ELBOW,
                LEFT_WRIST,
            )
        else:
            shoulder_index, elbow_index, wrist_index = (
                RIGHT_SHOULDER,
                RIGHT_ELBOW,
                RIGHT_WRIST,
            )

        shoulder = msg.poses[shoulder_index]
        elbow = msg.poses[elbow_index]
        wrist = msg.poses[wrist_index]

        keypoints = (shoulder, elbow, wrist)
        if not all(self.point_is_valid(pose) for pose in keypoints):
            self.matching_frames = 0
            return

        arm_extension = self.distance(shoulder, wrist)
        forward_reach = shoulder.position.z - wrist.position.z
        elbow_forward = shoulder.position.z - elbow.position.z

        offered = (
            arm_extension
            >= float(self.get_parameter("minimum_arm_extension_m").value)
            and forward_reach
            >= float(self.get_parameter("minimum_forward_reach_m").value)
            and elbow_forward > 0.0
        )

        self.matching_frames = self.matching_frames + 1 if offered else 0
        required_frames = int(self.get_parameter("required_frames").value)
        if self.matching_frames < required_frames:
            return

        now = self.get_clock().now()
        cooldown = float(self.get_parameter("cooldown_sec").value)
        if self.last_detection_time is not None:
            elapsed = (now - self.last_detection_time).nanoseconds / 1e9
            if elapsed < cooldown:
                return

        intent = String()
        intent.data = "handshake_offer"
        self.intent_publisher.publish(intent)
        self.last_detection_time = now
        self.matching_frames = 0
        self.get_logger().info("Detected social intent: handshake_offer")


def main(args=None):
    rclpy.init(args=args)
    node = GestureInterpreterNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
