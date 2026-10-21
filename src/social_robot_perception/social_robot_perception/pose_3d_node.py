#!/usr/bin/env python3

import math
from typing import Optional

import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Pose, PoseArray, PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from ultralytics import YOLO


COCO_KEYPOINT_COUNT = 17
LEFT_WRIST = 9
RIGHT_WRIST = 10


class Pose3DNode(Node):
    """Convert YOLO Pose keypoints into camera-frame 3D points."""

    def __init__(self):
        super().__init__("pose_3d_node")

        self.declare_parameter("color_topic", "/camera/color/image_raw")
        self.declare_parameter("depth_topic", "/camera/depth/image_raw")
        self.declare_parameter(
            "camera_info_topic", "/camera/color/camera_info"
        )
        self.declare_parameter("model_path", "yolo11n-pose.pt")
        self.declare_parameter("image_size", 640)
        self.declare_parameter("person_confidence", 0.35)
        self.declare_parameter("keypoint_confidence", 0.35)
        self.declare_parameter("depth_window_radius", 2)
        self.declare_parameter("max_depth_age_sec", 0.25)
        self.declare_parameter("wrist_side", "right")

        self.bridge = CvBridge()
        self.depth_image: Optional[np.ndarray] = None
        self.depth_stamp = None
        self.camera_info: Optional[CameraInfo] = None

        model_path = self.get_parameter("model_path").value
        self.model = YOLO(model_path)

        self.pose_publisher = self.create_publisher(
            PoseArray, "/person_pose_3d", 10
        )
        self.wrist_publisher = self.create_publisher(
            PoseStamped, "/wrist_pose", 10
        )

        self.create_subscription(
            Image,
            self.get_parameter("depth_topic").value,
            self.depth_callback,
            10,
        )
        self.create_subscription(
            CameraInfo,
            self.get_parameter("camera_info_topic").value,
            self.camera_info_callback,
            10,
        )
        self.create_subscription(
            Image,
            self.get_parameter("color_topic").value,
            self.color_callback,
            10,
        )

        self.get_logger().info("3D YOLO Pose node started.")

    def camera_info_callback(self, msg: CameraInfo):
        self.camera_info = msg

    def depth_callback(self, msg: Image):
        try:
            self.depth_image = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding="passthrough"
            )
            self.depth_stamp = msg.header.stamp
        except Exception as exc:
            self.get_logger().warning(f"Cannot decode depth image: {exc}")

    @staticmethod
    def stamp_seconds(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) / 1e9

    def depth_is_recent(self, color_msg: Image) -> bool:
        if self.depth_stamp is None:
            return False
        age = abs(
            self.stamp_seconds(color_msg.header.stamp)
            - self.stamp_seconds(self.depth_stamp)
        )
        return age <= float(self.get_parameter("max_depth_age_sec").value)

    def depth_metres(self, pixel_x: int, pixel_y: int) -> Optional[float]:
        if self.depth_image is None:
            return None

        height, width = self.depth_image.shape[:2]
        radius = int(self.get_parameter("depth_window_radius").value)
        x0 = max(0, pixel_x - radius)
        x1 = min(width, pixel_x + radius + 1)
        y0 = max(0, pixel_y - radius)
        y1 = min(height, pixel_y + radius + 1)
        values = np.asarray(self.depth_image[y0:y1, x0:x1]).reshape(-1)
        values = values[np.isfinite(values) & (values > 0)]
        if values.size == 0:
            return None

        depth = float(np.median(values))
        if np.issubdtype(self.depth_image.dtype, np.integer):
            depth /= 1000.0
        return depth

    def point_from_pixel(
        self, pixel_x: float, pixel_y: float, depth: float
    ) -> tuple[float, float, float]:
        info = self.camera_info
        fx, fy = info.k[0], info.k[4]
        cx, cy = info.k[2], info.k[5]
        x = (pixel_x - cx) * depth / fx
        y = (pixel_y - cy) * depth / fy
        return x, y, depth

    @staticmethod
    def invalid_pose() -> Pose:
        pose = Pose()
        pose.position.x = math.nan
        pose.position.y = math.nan
        pose.position.z = math.nan
        pose.orientation.w = 1.0
        return pose

    def color_callback(self, msg: Image):
        if self.camera_info is None or not self.depth_is_recent(msg):
            return

        try:
            color = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().warning(f"Cannot decode color image: {exc}")
            return

        result = self.model.predict(
            source=color,
            imgsz=int(self.get_parameter("image_size").value),
            conf=float(self.get_parameter("person_confidence").value),
            verbose=False,
        )[0]

        if result.keypoints is None or len(result.keypoints.xy) == 0:
            return

        keypoints = result.keypoints.xy[0].cpu().numpy()
        confidences = result.keypoints.conf[0].cpu().numpy()
        threshold = float(self.get_parameter("keypoint_confidence").value)

        color_height, color_width = color.shape[:2]
        depth_height, depth_width = self.depth_image.shape[:2]
        scale_x = depth_width / color_width
        scale_y = depth_height / color_height

        pose_array = PoseArray()
        pose_array.header = msg.header
        pose_array.header.frame_id = self.camera_info.header.frame_id

        for index in range(COCO_KEYPOINT_COUNT):
            confidence = float(confidences[index])
            if confidence < threshold:
                pose_array.poses.append(self.invalid_pose())
                continue

            color_x, color_y = keypoints[index]
            depth_x = int(round(color_x * scale_x))
            depth_y = int(round(color_y * scale_y))
            depth = self.depth_metres(depth_x, depth_y)
            if depth is None:
                pose_array.poses.append(self.invalid_pose())
                continue

            x, y, z = self.point_from_pixel(color_x, color_y, depth)
            pose = Pose()
            pose.position.x = x
            pose.position.y = y
            pose.position.z = z
            pose.orientation.w = 1.0
            pose_array.poses.append(pose)

        self.pose_publisher.publish(pose_array)

        wrist_side = str(self.get_parameter("wrist_side").value).lower()
        wrist_index = LEFT_WRIST if wrist_side == "left" else RIGHT_WRIST
        wrist = pose_array.poses[wrist_index]
        if math.isfinite(wrist.position.z):
            wrist_msg = PoseStamped()
            wrist_msg.header = pose_array.header
            wrist_msg.pose = wrist
            self.wrist_publisher.publish(wrist_msg)


def main(args=None):
    rclpy.init(args=args)
    node = Pose3DNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
