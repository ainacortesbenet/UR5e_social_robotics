import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
from ultralytics import YOLO
import cv2
import time
import sys
import os

# ==============================
# PARAMETERS
# ==============================
MODEL_PATH = "yolo11n-pose.pt"
# Canvia aquesta ruta pel nom exactament igual del fitxer de vídeo que has pujat
VIDEO_PATH = "Documentation/Images/Videos/handshake_test_video.mp4" 

IMG_SIZE = 640
CONF_THRESHOLD = 0.35
KEYPOINT_CONF_THRESHOLD = 0.35

# COCO keypoint indices
NOSE = 0
LEFT_WRIST = 9
RIGHT_WRIST = 10

class YoloPosePublisher(Node):
    def __init__(self):
        super().__init__('yolo_pose_publisher')
        # Publicador de ROS 2 per enviar la posició del canell al tòpic
        self.publisher_ = self.create_publisher(PointStamped, '/wrist_detection', 10)
        self.get_logger().info('Node YoloPosePublisher inicialitzat.')

    def publish_wrist(self, x, y, z=0.0):
        msg = PointStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'  # o el frame de referència de la teva càmera
        
        msg.point.x = float(x)
        msg.point.y = float(y)
        msg.point.z = float(z)
        
        self.publisher_.publish(msg)


def format_point(label, kpts, confs, idx):
    x, y = kpts[idx]
    conf = confs[idx]

    if conf < KEYPOINT_CONF_THRESHOLD:
        return f"{label}: not visible", None

    return f"{label}: x={x:.0f}, y={y:.0f}, c={conf:.2f}", (x, y)


def main(args=None):
    # Inicialització de ROS 2
    rclpy.init(args=args)
    ros_node = YoloPosePublisher()

    # Càrrega del model YOLO
    print("Carregant model YOLO...")
    model = YOLO(MODEL_PATH)

    # Comprovació del fitxer de vídeo
    if not os.path.exists(VIDEO_PATH):
        print(f"Error: No s'ha trobat el fitxer de vídeo a: {os.path.abspath(VIDEO_PATH)}")
        print("Assegura't de posar la ruta correcta del vídeo pujat.")
        sys.exit(1)

    cap = cv2.VideoCapture(VIDEO_PATH)

    if not cap.isOpened():
        print(f"Error: No s'ha pogut obrir el vídeo {VIDEO_PATH}")
        sys.exit(1)

    print(f"Vídeo '{VIDEO_PATH}' obert correctament.")
    print("Processant fotogrames i publicant a ROS 2 (/wrist_detection)... Press Ctrl+C to quit.")

    try:
        while rclpy.ok():
            ret, frame = cap.read()

            # Si el vídeo arriba al final, torna a començar en bucle (Loop)
            if not ret:
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

            if result.keypoints is not None and result.keypoints.xy is not None:
                kpts_all = result.keypoints.xy.cpu().numpy()
                confs_all = result.keypoints.conf.cpu().numpy()

                if len(kpts_all) > 0:
                    # Agafem la primera persona detectada
                    kpts = kpts_all[0]
                    confs = confs_all[0]

                    str_rw, right_wrist_pt = format_point("right_wrist", kpts, confs, RIGHT_WRIST)
                    str_lw, left_wrist_pt = format_point("left_wrist", kpts, confs, LEFT_WRIST)

                    # Triem el canell dret si està visible, sinó l'esquerre
                    target_pt = right_wrist_pt if right_wrist_pt else left_wrist_pt
                    
                    if target_pt:
                        wx, wy = target_pt
    
                        # ------------------------------------------------------------------
                        # MAPEIG DE PÍXELS A L'ESPAI REAL DEL ROBOT (UR5e WORKSPACE)
                        # ------------------------------------------------------------------
                        # Convertim x (píxels 0..640) a l'eix X del robot (ex: de -250 mm a +250 mm)
                        x_robot = ((wx / 640.0) * 500.0) - 250.0
                        
                        # Posem una distància Y frontal reachable (ex: -400 mm respecte la base)
                        y_robot = -400.0
                        
                        # Posem una alçada Z segura per sobre de la taula (ex: 200 mm)
                        z_robot = 200.0
                        
                        print(f"[YOLO MAPPED] Pixels: ({wx:.0f}, {wy:.0f}) -> Robot Workspace: X={x_robot:.1f}, Y={y_robot:.1f}, Z={z_robot:.1f}")
                        
                        # Publica les coordenades adaptades
                        ros_node.publish_wrist(x=x_robot, y=y_robot, z=z_robot)
                        
                    else:
                        print("Canell no visible en aquest fotograma.")

            # Processa esdeveniments de ROS 2 sense bloquejar
            rclpy.spin_once(ros_node, timeout_sec=0.001)
            
            # Petita pausa per adaptar els FPS
            time.sleep(0.03)

    except KeyboardInterrupt:
        print("\nAturat per l'usuari (Ctrl+C)")

    finally:
        cap.release()
        ros_node.destroy_node()
        rclpy.shutdown()
        print("Càmera/Vídeo alliberat i node tancat correctament.")

if __name__ == '__main__':
    main()