#!/usr/bin/env python3

import math
import socket
import time
from pathlib import Path

from robodk.robolink import ITEM_TYPE_FRAME, ITEM_TYPE_ROBOT, Robolink
from robodk.robomath import Pose_2_UR, rotx, roty, rotz, transl

from config import EXECUTION_MODE, ROBOT_IP, ROBOT_PORT

VALID_EXECUTION_MODES = {
    "simulation_only",
    "simulation_and_real",
    "real_only",
}

BASE_DIR = Path(__file__).resolve().parent
RDK_FILE = BASE_DIR / "resources" / "roboDK" / "Social_UR5e.rdk"
ROBOT_NAME = "UR5e"
BASE_NAME = "UR5e Base"
TOOL_NAME = "Hand"


class RobotController:
    def __init__(self):
        if EXECUTION_MODE not in VALID_EXECUTION_MODES:
            allowed = ", ".join(sorted(VALID_EXECUTION_MODES))
            raise ValueError(
                f"Invalid EXECUTION_MODE in config.py: {EXECUTION_MODE!r}. "
                f"Choose one of: {allowed}"
            )
        self.robot_socket = None
        self.real_robot_connected = False
        print("Loading RoboDK...")
        self.rdk = Robolink()
        time.sleep(2)
        self.load_station()
        self.load_items()
        self.connect_robot()
        self.set_tcp_from_robodk()

    def load_station(self):
        if not RDK_FILE.exists():
            raise FileNotFoundError(f"RoboDK station not found: {RDK_FILE}")
        self.rdk.AddFile(str(RDK_FILE))
        time.sleep(2)

    def load_items(self):
        self.robot = self.rdk.Item(ROBOT_NAME, ITEM_TYPE_ROBOT)
        self.base = self.rdk.Item(BASE_NAME, ITEM_TYPE_FRAME)
        self.tool = self.rdk.Item(TOOL_NAME)
        if not self.robot.Valid():
            raise RuntimeError(f"Robot item not found: {ROBOT_NAME}")
        if not self.base.Valid():
            raise RuntimeError(f"Base frame not found: {BASE_NAME}")
        if not self.tool.Valid():
            raise RuntimeError(f"Tool not found: {TOOL_NAME}")
        self.robot.setPoseFrame(self.base)
        self.robot.setPoseTool(self.tool)
        print("RoboDK station loaded correctly.")

    def connect_robot(self):
        try:
            self.robot_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.robot_socket.settimeout(2.0)
            self.robot_socket.connect((ROBOT_IP, ROBOT_PORT))
            self.real_robot_connected = True
            print(f"Connected to real UR5e at {ROBOT_IP}:{ROBOT_PORT}")
        except Exception as error:
            print(f"Robot connection failed: {error}")
            print("The server will use RoboDK simulation when possible.")
            self.robot_socket = None
            self.real_robot_connected = False

    def send_script(self, script, wait_time=0.0):
        if not self.real_robot_connected:
            print("Real UR5e not connected. URScript not sent.")
            return False
        try:
            self.robot_socket.sendall((script.strip() + "\n").encode("utf-8"))
            print("[URSCRIPT]", script)
            if wait_time > 0:
                time.sleep(wait_time)
            return True
        except Exception as error:
            print(f"Error sending URScript: {error}")
            self.real_robot_connected = False
            return False

    def set_tcp_from_robodk(self):
        if not self.real_robot_connected:
            return
        x, y, z, rx, ry, rz = Pose_2_UR(self.robot.PoseTool())
        script = (
            f"set_tcp(p[{x/1000.0:.6f},{y/1000.0:.6f},{z/1000.0:.6f},"
            f"{rx:.6f},{ry:.6f},{rz:.6f}])"
        )
        self.send_script(script, wait_time=1.0)

    @staticmethod
    def build_movej_script(joints_deg, a=1.2, v=0.5, t=-1, r=0.0):
        values = ",".join(f"{math.radians(q):.6f}" for q in joints_deg)
        if t is not None and t >= 0:
            return f"movej([{values}], a={a}, v={v}, t={t}, r={r})", t
        return f"movej([{values}], a={a}, v={v}, r={r})", 0.0

    @staticmethod
    def build_movel_script(xyz_mm, rpy_deg, a=1.2, v=0.15, t=-1, r=0.0):
        x, y, z = xyz_mm
        roll, pitch, yaw = rpy_deg
        pose = transl(x, y, z) * rotx(math.radians(roll)) * roty(math.radians(pitch)) * rotz(math.radians(yaw))
        x, y, z, rx, ry, rz = Pose_2_UR(pose)
        values = f"{x/1000.0:.6f},{y/1000.0:.6f},{z/1000.0:.6f},{rx:.6f},{ry:.6f},{rz:.6f}"
        if t is not None and t >= 0:
            return f"movel(p[{values}], a={a}, v={v}, t={t}, r={r})", t
        return f"movel(p[{values}], a={a}, v={v}, r={r})", 0.0

    def movej(self, joints_deg, a=1.2, v=0.5, t=-1, r=0.0):
        script, wait_time = self.build_movej_script(joints_deg, a, v, t, r)
        success = True
        if EXECUTION_MODE in ("simulation_only", "simulation_and_real"):
            self.robot.MoveJ(joints_deg)
        if EXECUTION_MODE in ("real_only", "simulation_and_real"):
            success = self.send_script(script, wait_time) if self.real_robot_connected else False
        return success

    def movel_pose(self, xyz_mm, rpy_deg, a=1.2, v=0.15, t=-1, r=0.0):
        script, wait_time = self.build_movel_script(xyz_mm, rpy_deg, a, v, t, r)
        success = True
        if EXECUTION_MODE in ("simulation_only", "simulation_and_real"):
            x, y, z = xyz_mm
            roll, pitch, yaw = rpy_deg
            pose = transl(x, y, z) * rotx(math.radians(roll)) * roty(math.radians(pitch)) * rotz(math.radians(yaw))
            self.robot.MoveL(pose)
        if EXECUTION_MODE in ("real_only", "simulation_and_real"):
            success = self.send_script(script, wait_time) if self.real_robot_connected else False
        return success

    def execute_sequence(self, data):
        if not isinstance(data, dict) or "steps" not in data:
            raise RuntimeError("YAML file does not contain 'steps'")
        print("\nExecuting sequence:", data.get("sequence_name", "unnamed"))
        print(f"Execution mode: {EXECUTION_MODE}")
        for step in data["steps"]:
            options = {
                "a": step.get("acceleration", 1.2),
                "v": step.get("velocity", 0.25),
                "t": step.get("time", -1),
                "r": step.get("blend", 0.0),
            }
            if step["motion"] == "moveJ":
                ok = self.movej(step["joints_deg"], **options)
            elif step["motion"] == "moveL":
                ok = self.movel_pose(step["target_xyz_mm"], step["target_rpy_deg"], **options)
            else:
                raise RuntimeError(f"Unknown motion type: {step['motion']}")
            if not ok:
                raise RuntimeError(f"Motion step failed: {step.get('name', 'unnamed_step')}")
        print("Sequence completed successfully.")

    def shutdown(self):
        if self.robot_socket:
            self.robot_socket.close()
        try:
            self.rdk.CloseRoboDK()
        except Exception:
            pass
