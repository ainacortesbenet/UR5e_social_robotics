import rclpy
from rclpy.node import Node
import yaml
import os
import subprocess

class HandshakeExecutor(Node):
    def __init__(self):
        super().__init__('handshake_executor')
        self.get_logger().info('Node Handshake Executor iniciat.')

    def generar_yaml_dinamic(self, wrist_x, wrist_y, wrist_z, offset_z=100.0):
        # Definim les rutes directament a la carpeta config local
        # (Tres os.path.dirname pugen des d'aquest fitxer fins a la carpeta arrel del paquet)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_dir = os.path.join(base_dir, 'config')

        ruta_yaml_original = os.path.join(config_dir, 'handshake_sequence.yaml')
        ruta_yaml_generat = os.path.join(config_dir, 'handshake_execution_generated.yaml')

        if not os.path.exists(ruta_yaml_original):
            self.get_logger().error(f"No s'ha trobat el fitxer base a: {ruta_yaml_original}")
            return None

        with open(ruta_yaml_original, 'r') as f:
            config = yaml.safe_load(f)
        
        # AJUST MANUAL DE L'OFFSET DE LA TAULA RESPECTE A BASE_LINK
        # =========================================================================
        # Si la taula està, per exemple, 150 mm per sota de la base del robot:
        offset_taula_z = 0.0  # Canvia aquest valor si la taula està més amunt/avall
        offset_taula_x = 0.0  # Canvia si la taula està desplaçada en X
        offset_taula_y = 0.0  # Canvia si la taula està desplaçada en Y

        # Apliquem la conversió a les coordenades rebudes:
        x_corregida = float(wrist_x) + offset_taula_x
        y_corregida = float(wrist_y) + offset_taula_y
        z_corregida = float(wrist_z) + offset_taula_z

        # Guardem els punts ja convertits per al robot:
        target_handshake = [x_corregida, y_corregida, z_corregida]
        target_approach = [x_corregida, y_corregida, z_corregida + offset_z]

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
            
            # 1. Rutes absolutes al fitxer YAML generat
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ruta_yaml_absoluta = os.path.join(base_dir, 'config', 'handshake_execution_generated.yaml')
            
            # 2. Ruta a l'script ur5e_pose_sequence.py directament
            script_pose_seq = os.path.join(base_dir, 'ur5e_robot_controller', 'ur5e_pose_sequence.py')
            
            # 3. Executem l'script de la seqüència passant-li la ruta del YAML
            comanda = f'python3 "{script_pose_seq}" --ros-args -p sequence_file:="{ruta_yaml_absoluta}"'
            
            self.get_logger().info(f"Executant comanda: {comanda}")
            subprocess.run(comanda, shell=True)

def main(args=None):
    rclpy.init(args=args)
    node = HandshakeExecutor()

    posicio_canell_detectada = {'x': -280.0, 'y': -320.0, 'z': 210.0}

    node.executar_handshake(
        posicio_canell_detectada['x'],
        posicio_canell_detectada['y'],
        posicio_canell_detectada['z']
    )

    rclpy.shutdown()

if __name__ == '__main__':
    main()