#!/usr/bin/env python3

# behavior_manager.py

import socket
from pathlib import Path
from typing import Optional

from config import SERVER_IP, SERVER_PORT
from utils.yaml_loader import load_yaml_file

BASE_DIR = Path(__file__).resolve().parent
MOTIONS_DIR = BASE_DIR / "motions"

MOTIONS = {
    "init": "motions/init.yaml",
    "handshake": "motions/handshake.yaml",
    "give5": "motions/give5.yaml",
}


class BehaviorManager:

    def __init__(self):
        self.server_ip = SERVER_IP
        self.server_port = SERVER_PORT

    def get_motion_file(self, command: str) -> Optional[str]:
        return MOTIONS.get(command)

    def available_motions(self):
        """Return the registered motion names exposed to all client interfaces."""
        return sorted(MOTIONS)

    def execute_command(self, command: str) -> bool:

        if command == "exit":
            print("[BEHAVIOR] Exit command received.")
            return True
        
        motion_file = self.get_motion_file(command)

        if motion_file is None:
            print(f"[BEHAVIOR] Unknown command: {command}")
            return False

        motion_path = BASE_DIR / motion_file

        try:
            load_yaml_file(motion_path)
        except Exception as e:
            print(f"[BEHAVIOR] Invalid YAML file: {e}")
            return False

        return self.send_motion_file(motion_path)

    def send_motion_file(self, motion_file: Path) -> bool:
        try:
            with open(motion_file, "r", encoding="utf-8") as f:
                yaml_text = f.read()

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(15.0)
            sock.connect((self.server_ip, self.server_port))

            sock.sendall(yaml_text.encode("utf-8"))
            sock.shutdown(socket.SHUT_WR)

            response = sock.recv(4096).decode("utf-8")
            print(f"[SERVER RESPONSE] {response.strip()}")

            sock.close()
            # Returns true if server response starts with "OK", indicating successful execution
            return response.startswith("OK")

        except Exception as e:
            print(f"[BEHAVIOR] Error sending motion file: {e}")
            return False
