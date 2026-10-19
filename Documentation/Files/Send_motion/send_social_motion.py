#!/usr/bin/env python3

import subprocess
from pathlib import Path

# -------------------------
# CONFIGURACIÓ
# -------------------------

PROFESSOR_IP = "192.168.0.10"
PROFESSOR_USER = "student"

LOCAL_FOLDER = "/home/student/UR5e_social_robotics/src/social_robot_behaviors/motions/"
REMOTE_FOLDER = "/home/biorob/UR5e_social_robotics/install/social_robot_behaviors/share/social_robot_behaviors/motions/"

# -------------------------

filename = input("Nom del fitxer YAML: ")

local_file = Path(LOCAL_FOLDER) / filename

if not local_file.exists():
    print(f"Error: {local_file} no existeix.")
    exit(1)

cmd = [
    "scp",
    str(local_file),
    f"{PROFESSOR_USER}@{PROFESSOR_IP}:{REMOTE_FOLDER}"
]

print("Copiant fitxer...")

try:
    subprocess.run(cmd, check=True)
    print("Fitxer copiat correctament.")
except subprocess.CalledProcessError:
    print("Error en la còpia.")
