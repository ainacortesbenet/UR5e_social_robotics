import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
from ultralytics import YOLO
import cv2
import time
import sys
import os

# ==============================
# PARAMETERS & PATHS
# ==============================
# Troba la carpeta arrel del workspace de forma dinàmica
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Pujem nivells fins a trobar l'arrel (~/UR5e_social_robotics)
WORKSPACE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))

MODEL_PATH = os.path.join(SCRIPT_DIR, "yolo11n-pose.pt")
VIDEO_PATH = os.path.join(WORKSPACE_DIR, "Documentation", "Images", "Videos", "handshake_test_video.mp4")

IMG_SIZE = 640
CONF_THRESHOLD = 0.35
KEYPOINT_CONF_THRESHOLD = 0.35

# COCO keypoint indices
NOSE = 0
LEFT_WRIST = 9
RIGHT_WRIST = 10


def format_point(label, kpts, confs, idx):
    x, y = kpts[idx]
    conf = confs[idx]

    if conf < KEYPOINT_CONF_THRESHOLD:
        return f"{label}: not visible", None

    return f"{label}: x={x:.0f}, y={y:.0f}, c={conf:.2f}", (x, y)


def draw_left_info_panel(frame, lines):
    panel_width = 420

    panel = frame[:, :panel_width].copy()
    panel[:] = (30, 30, 30)

    y = 45

    cv2.putText(
        panel,
        "POSE DATA",
        (20, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    y += 50

    for line in lines:
        cv2.putText(
            panel,
            line,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        y += 38

    return cv2.hconcat([panel, frame])


# ==============================
# ROS 2 NODE CLASS
# ==============================
class YoloWristPublisher(Node):
    def __init__(self):
        super().__init__('yolo_wrist_publisher')
        self.publisher_ = self.create_publisher(PointStamped, '/wrist_detection', 10)
        self.get_logger().info('Node YoloWristPublisher iniciat i publicant a /wrist_detection')

    def publish_wrist(self, x_pixel, y_pixel):
        # Mapeig de píxels (0..640) a l'espai accessible del robot UR5e (mm)
        x_robot = ((x_pixel / 640.0) * 500.0) - 250.0
        y_robot = -400.0  # Distància frontal fixa
        z_robot = 200.0   # Altura Z segura sobre la taula

        msg = PointStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.point.x = float(x_robot)
        msg.point.y = float(y_robot)
        msg.point.z = float(z_robot)

        self.publisher_.publish(msg)


# ==============================
# MAIN EXECUTION
# ==============================
def main(args=None):
    # Inicialització de ROS 2
    rclpy.init(args=args)
    ros_node = YoloWristPublisher()

    # Load Model
    if not os.path.exists(MODEL_PATH):
        print(f"Error: no s'ha trobat el model a {MODEL_PATH}")
        sys.exit(1)
        
    model = YOLO(MODEL_PATH)

    # Open Video File (en lloc de la webcam fisica)
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: no s'ha trobat el fitxer de vídeo a {VIDEO_PATH}")
        sys.exit(1)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: no s'ha pogut obrir el vídeo {VIDEO_PATH}")
        sys.exit(1)

    print(f"Fitxer de vídeo obert correctament des de: {VIDEO_PATH}")
    print("Premeu 'q' per sortir o Ctrl+C")

    try:
        while rclpy.ok():
            ret, frame = cap.read()

            if not ret:
                # Quan arriba al final del vídeo, torna al primer fotograma (Loop)
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue

            start_time = time.perf_counter()

            results = model.predict(
                source=frame,
                imgsz=IMG_SIZE,
                conf=CONF_THRESHOLD,
                verbose=False,
            )

            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            result = results[0]
            annotated_frame = result.plot()

            lines = [
                "head: not visible",
                "left_wrist: not visible",
                "right_wrist: not visible",
            ]

            if result.keypoints is not None and result.keypoints.xy is not None:
                kpts_all = result.keypoints.xy.cpu().numpy()
                confs_all = result.keypoints.conf.cpu().numpy()

                if len(kpts_all) > 0:
                    kpts = kpts_all[0]
                    confs = confs_all[0]

                    str_head, _ = format_point("head", kpts, confs, NOSE)
                    str_lw, pt_lw = format_point("left_wrist", kpts, confs, LEFT_WRIST)
                    str_rw, pt_rw = format_point("right_wrist", kpts, confs, RIGHT_WRIST)

                    lines = [str_head, str_lw, str_rw]

                    # Prioritzem el canell dret, sinó l'esquerre
                    target_pt = pt_rw if pt_rw else pt_lw

                    if target_pt:
                        wx, wy = target_pt
                        # Publicació de les coordenades a ROS 2
                        ros_node.publish_wrist(wx, wy)

            lines.append(f"time: {elapsed_ms:.1f} ms")

            output_frame = draw_left_info_panel(annotated_frame, lines)

            # Visualització de la imatge si la finestra GUI està disponible
            try:
                cv2.imshow("YOLO Pose - Head and Wrists", output_frame)
                key = cv2.waitKey(30) & 0xFF
                if key == ord("q"):
                    print("Exit requested with q")
                    break
            except cv2.error:
                pass

            # Processa esdeveniments de ROS 2
            rclpy.spin_once(ros_node, timeout_sec=0.001)

    except KeyboardInterrupt:
        print("\nExit requested with Ctrl+C")

    finally:
        cap.release()
        cv2.destroyAllWindows()
        ros_node.destroy_node()
        rclpy.shutdown()
        print("Recursos tancats correctament")


if __name__ == '__main__':
    main()