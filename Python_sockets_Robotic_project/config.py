# config.py

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5000

ROBOT_IP = "192.168.0.20"
ROBOT_PORT = 30002

# "simulation_only", "simulation_and_real" or "real_only"
EXECUTION_MODE = "simulation_only"

#RDK_FILE = "src/roboDK/Social_UR5e.rdk"

MOTIONS_DIR = "motions"

ACTIVATION_WORD = "robot"
LANGUAGE = "en-US"
TTS_RATE = 170

# Optional face-verification interface.
REFERENCE_FACE_IMAGE = "resources/Pictures/Aina_ref.jpeg"
CAMERA_INDEX = 0
FACE_MATCH_TOLERANCE = 0.6

MAX_YAML_SIZE_BYTES = 20000
