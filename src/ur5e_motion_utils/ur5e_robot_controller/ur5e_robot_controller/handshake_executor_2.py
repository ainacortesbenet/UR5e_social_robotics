import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PointStamped
import yaml
import os
import subprocess

class HandshakeExecutor(Node):
    def __init__(self):
        super().__init__('handshake_executor')
        self.get_logger().info('Node Handshake Executor iniciat. Esperant dades del tòpic /wrist_detection...')

        # Variable de seguretat per no llançar el moviment 30 vegades per segon mentre s'executa
        self.executant_moviment = False

        # SUBSCRIBER: Escolta el tòpic enviat pel teu script de YOLO Pose
        self.subscription = self.create_subscription(
            PointStamped,
            '/wrist_detection',          # Tòpic on el vídeo emet la posició
            self.wrist_callback,         # Funció que es crida quan arriben coordenades
            10
        )

    def wrist_callback(self, msg):
        """S'executa automàticament cada vegada que arriba una nova posició del canell."""
        if self.executant_moviment:
            # Si el robot ja està fent el moviment, ignorem noves coordenades
            return

        # Obtenim la posició (X, Y, Z) enviada per YOLO
        wrist_x = msg.point.x
        wrist_y = msg.point.y
        wrist_z = msg.point.z

        self.get_logger().info(f"Nova mà rebuida del tòpic -> X={wrist_x:.1f}, Y={wrist_y:.1f}, Z={wrist_z:.1f}")

        # Bloquegem temporitzador i executem el handshake
        self.executant_moviment = True
        self.executar_handshake(wrist_x, wrist_y, wrist_z)
        self.executant_moviment = False

    def generar_yaml_dinamic(self, wrist_x, wrist_y, wrist_z, offset_z=100.0):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(base_dir, 'config')

        ruta_yaml_original = os.path.join(config_dir, 'handshake_sequence.yaml')
        ruta_yaml_generat = os.path.join(config_dir, 'handshake_execution_generated.yaml')

        if not os.path.exists(ruta_yaml_original):
            self.get_logger().error(f"No s'ha trobat el fitxer base a: {ruta_yaml_original}")
            return None

        with open(ruta_yaml_original, 'r') as f:
            config = yaml.safe_load(f)

        target_handshake = [float(wrist_x), float(wrist_y), float(wrist_z)]
        target_approach = [float(wrist_x), float(wrist_y), float(wrist_z) + offset_z]

        for step in config['steps']:
            if step['name'] in ['approach_handshake', 'retreat_handshake']:
                step['target_xyz'] = target_approach
            elif step['name'] == 'handshake':
                step['target_xyz'] = target_handshake

        with open(ruta_yaml_generat, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        self.get_logger().info(f"YAML generat correctament a: {ruta_yaml_generat}")
        return 'handshake_execution_generated.yaml'

    def executar_handshake(self, x, y, z):
        yaml_final = self.generar_yaml_dinamic(x, y, z)
        
        if yaml_final:
            self.get_logger().info(f"Enviant comanda de moviment al robot cap a: X={x}, Y={y}, Z={z}")
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_yaml_absoluta = os.path.join(base_dir, 'config', 'handshake_execution_generated.yaml')
            script_pose_seq = os.path.join(base_dir, 'ur5e_robot_controller', 'ur5e_pose_sequence.py')
            
            comanda = f'python3 "{script_pose_seq}" --ros-args -p sequence_file:="{ruta_yaml_absoluta}"'
            subprocess.run(comanda, shell=True)

def main(args=None):
    rclpy.init(args=args)
    node = HandshakeExecutor()

    try:
        # A diferència de la versió 'mocked', rclpy.spin manté el node obert escoltant el tòpic
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()