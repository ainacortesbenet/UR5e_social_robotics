import rclpy
from rclpy.node import Node
import yaml
import os

class HandshakeExecutor(Node):
    def __init__(self):
        super().__init__('handshake_executor')
        self.get_logger().info('Node Handshake Executor iniciat.')

    def generar_yaml_dinamic(self, wrist_x, wrist_y, wrist_z, offset_z=100.0):
        """
        Rep les coordenades del canell i actualitza l'estructura de passos.
        """
        ruta_yaml_original = 'handshake_sequence.yaml'
        ruta_yaml_generat = 'handshake_execution_generated.yaml'

        # 1. Llegir el YAML base
        if not os.path.exists(ruta_yaml_original):
            self.get_logger().error(f"No s'ha trobat el fitxer {ruta_yaml_original}")
            return False

        with open(ruta_yaml_original, 'r') as f:
            config = yaml.safe_load(f)

        # 2. Definir posicions basades en el canell detectat
        target_handshake = [float(wrist_x), float(wrist_y), float(wrist_z)]
        target_approach = [float(wrist_x), float(wrist_y), float(wrist_z) + offset_z]

        # 3. Assignar els valors als passos corresponents
        for step in config['steps']:
            if step['name'] in ['approach_handshake', 'retreat_handshake']:
                step['target_xyz'] = target_approach
            elif step['name'] == 'handshake':
                step['target_xyz'] = target_handshake

        # 4. Desar el fitxer temporal actualitzat
        with open(ruta_yaml_generat, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        self.get_logger().info(f"YAML generat amb èxit a: {ruta_yaml_generat}")
        return ruta_yaml_generat

    def executar_handshake(self, x, y, z):
        # Generar la configuració per a aquest moviment
        yaml_final = self.generar_yaml_dinamic(x, y, z)
        
        if yaml_final:
            self.get_logger().info(f"Enviant comanda de moviment al robot cap a: X={x}, Y={y}, Z={z}")
            # AQUÍ crides al teu controlador existent de ROS 2 per carregar el YAML generat.
            # Exemple: os.system(f"ros2 launch el_teu_paquet executar_trajectoria.launch.py config_file:={yaml_final}")

def main(args=None):
    rclpy.init(args=args)
    node = HandshakeExecutor()

    # EXEMPLE: Suposem que la càmera detecta el canell a (-280, -320, 210) mm
    posicio_canell_detectada = {'x': -280.0, 'y': -320.0, 'z': 210.0}

    node.executar_handshake(
        posicio_canell_detectada['x'],
        posicio_canell_detectada['y'],
        posicio_canell_detectada['z']
    )

    rclpy.shutdown()

if __name__ == '__main__':
    main()