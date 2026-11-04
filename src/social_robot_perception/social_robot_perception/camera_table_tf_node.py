#!/usr/bin/env python3

"""Publish the calibrated static transform from the robot table to Gemini2."""

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def quaternion_from_rpy(roll, pitch, yaw):
    """Return a quaternion from roll, pitch and yaw in radians."""
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * sy + sr * sp * cy,
    )


class CameraTableTfNode(Node):
    """Publish ``table -> camera`` only after its calibration is enabled."""

    def __init__(self):
        super().__init__("camera_table_tf_node")

        self.declare_parameter("enabled", False)
        self.declare_parameter("parent_frame", "table")
        self.declare_parameter("child_frame", "camera_color_optical_frame")
        self.declare_parameter("translation_m", [0.0, 0.0, 0.0])
        self.declare_parameter("rpy_rad", [0.0, 0.0, 0.0])

        if not self.get_parameter("enabled").value:
            self.get_logger().error(
                "Camera-to-table calibration is disabled. Set enabled:=true only "
                "after entering measured translation_m and rpy_rad values."
            )
            return

        translation = self.get_parameter("translation_m").value
        rpy = self.get_parameter("rpy_rad").value
        if len(translation) != 3 or len(rpy) != 3:
            raise ValueError("translation_m and rpy_rad must each contain 3 values")

        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.get_parameter("parent_frame").value
        transform.child_frame_id = self.get_parameter("child_frame").value
        transform.transform.translation.x = float(translation[0])
        transform.transform.translation.y = float(translation[1])
        transform.transform.translation.z = float(translation[2])
        (
            transform.transform.rotation.x,
            transform.transform.rotation.y,
            transform.transform.rotation.z,
            transform.transform.rotation.w,
        ) = quaternion_from_rpy(float(rpy[0]), float(rpy[1]), float(rpy[2]))

        self.broadcaster = StaticTransformBroadcaster(self)
        self.broadcaster.sendTransform(transform)
        self.get_logger().info(
            "Published calibrated transform %s -> %s"
            % (transform.header.frame_id, transform.child_frame_id)
        )


def main(args=None):
    rclpy.init(args=args)
    node = CameraTableTfNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
