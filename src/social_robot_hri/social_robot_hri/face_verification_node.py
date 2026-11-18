#!/usr/bin/env python3
"""Authorise once by face, then gate HRI behavior requests."""

from pathlib import Path

import cv2
import face_recognition
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSPresetProfiles
from sensor_msgs.msg import Image
from std_msgs.msg import String


class FaceVerifier:
    """Compare camera faces with one reference image."""

    def __init__(self, reference_image, camera_index=0, tolerance=0.6):
        self.reference_image = Path(reference_image).expanduser()
        self.camera_index = camera_index
        self.tolerance = tolerance

    def verify(self, read_frame=None):
        if not self.reference_image.is_file():
            raise FileNotFoundError(
                f'Reference image not found: {self.reference_image}'
            )

        image = face_recognition.load_image_file(str(self.reference_image))
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            raise RuntimeError('No face found in the reference image.')

        camera = None
        if read_frame is None:
            camera = cv2.VideoCapture(self.camera_index)
            if not camera.isOpened():
                camera.release()
                raise RuntimeError(f'Camera {self.camera_index} is not available.')
            read_frame = camera.read

        print('[FACE] Look at the camera. Press Q to cancel.')
        try:
            while rclpy.ok():
                ok, frame = read_frame()
                if not ok:
                    continue

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                faces = face_recognition.face_encodings(rgb_frame)
                authorised = bool(faces) and face_recognition.compare_faces(
                    [encodings[0]], faces[0], tolerance=self.tolerance
                )[0]

                label = 'AUTHORISED' if authorised else 'UNKNOWN'
                color = (0, 255, 0) if authorised else (0, 0, 255)
                cv2.putText(
                    frame, label, (30, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, color, 2
                )
                cv2.imshow('Face verification', frame)

                if authorised:
                    cv2.waitKey(750)
                    return True
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    return False
            return False
        finally:
            if camera is not None:
                camera.release()
            cv2.destroyAllWindows()


class FaceVerificationNode(Node):
    def __init__(self):
        super().__init__('face_verification_node')
        self.declare_parameter('reference_image', '')
        self.declare_parameter('camera_index', 0)
        self.declare_parameter('image_topic', '')
        self.declare_parameter('tolerance', 0.6)
        self.declare_parameter('input_topic', '/social_behavior/request')
        self.declare_parameter('output_topic', '/social_behavior')

    def verify_user(self):
        reference_image = str(self.get_parameter('reference_image').value)
        if not reference_image:
            raise RuntimeError('Set the reference_image ROS parameter.')

        verifier = FaceVerifier(
            reference_image,
            camera_index=int(self.get_parameter('camera_index').value),
            tolerance=float(self.get_parameter('tolerance').value),
        )
        image_topic = self.get_parameter('image_topic').value
        if image_topic:
            self.latest_image = None
            qos = QoSPresetProfiles.SENSOR_DATA.value
            qos.depth = 1
            subscription = self.create_subscription(Image, image_topic, self.image_callback, qos)
            self.get_logger().info(f'Waiting for colour images on {image_topic}')
            try:
                self.authorised = verifier.verify(self.read_topic_frame)
            finally:
                self.destroy_subscription(subscription)
        else:
            self.authorised = verifier.verify()

        if not self.authorised:
            self.get_logger().error('Face verification failed. Requests are blocked.')
        else:
            self.get_logger().info('User authorised. HRI requests are enabled.')

        self.publisher_ = self.create_publisher(
            String, str(self.get_parameter('output_topic').value), 10
        )
        self.subscription = self.create_subscription(
            String,
            str(self.get_parameter('input_topic').value),
            self.request_callback,
            10,
        )

    def image_callback(self, msg):
        self.latest_image = msg

    def read_topic_frame(self):
        rclpy.spin_once(self, timeout_sec=0.25)
        msg = self.latest_image
        self.latest_image = None
        if msg is None:
            return False, None
        if msg.encoding not in ('rgb8', 'bgr8'):
            raise RuntimeError(f'Unsupported colour image encoding: {msg.encoding}')

        row_bytes = msg.width * 3
        if not msg.width or not msg.height or msg.step < row_bytes:
            raise RuntimeError('Invalid colour image dimensions or row stride.')
        if len(msg.data) != msg.height * msg.step:
            raise RuntimeError('Invalid colour image buffer size.')

        # ROS image rows can contain padding after the last pixel.
        rows = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
        frame = rows[:, :row_bytes].reshape(msg.height, msg.width, 3)
        if msg.encoding == 'rgb8':
            return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame.copy()

    def request_callback(self, msg):
        if not self.authorised:
            self.get_logger().warn('Rejected behavior request: user not authorised.')
            return
        self.publisher_.publish(msg)
        self.get_logger().info(f'Authorised behavior: {msg.data}')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = FaceVerificationNode()
        node.verify_user()
        if rclpy.ok():
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except (RuntimeError, FileNotFoundError) as error:
        print(f'[FACE] {error}')
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
