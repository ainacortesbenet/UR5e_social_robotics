#!/usr/bin/env python3

import socket
import threading

from ur5e_robot_controller import RobotController
from utils.yaml_loader import load_yaml_text


SERVER_IP = "0.0.0.0"
SERVER_PORT = 5000
MAX_YAML_SIZE_BYTES = 20000
robot_lock = threading.Lock()


def receive_all(conn):
    chunks = []
    total_size = 0
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            break
        chunks.append(chunk)
        total_size += len(chunk)
        if total_size > MAX_YAML_SIZE_BYTES:
            raise RuntimeError("YAML file too large")
    return b"".join(chunks).decode("utf-8")


def handle_client(conn, addr, robot):
    print(f"\nConnection from {addr}")
    try:
        yaml_text = receive_all(conn)
        print("\nReceived YAML:")
        print(yaml_text)
        data = load_yaml_text(yaml_text)

        if not robot_lock.acquire(blocking=False):
            response = "ERROR: Robot is busy. Try again later.\n"
        else:
            try:
                robot.execute_sequence(data)
                response = "OK: sequence executed\n"
            finally:
                robot_lock.release()
    except Exception as error:
        response = f"ERROR: {error}\n"
        print(response)

    conn.sendall(response.encode("utf-8"))
    conn.close()


def main():
    robot = RobotController()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.settimeout(1.0)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(5)
    print(f"\nUR5e classroom server listening on {SERVER_IP}:{SERVER_PORT}")

    try:
        while True:
            try:
                conn, addr = server_socket.accept()
            except socket.timeout:
                if not robot.is_robodk_running():
                    print("\nRoboDK closed. Stopping server...")
                    break
                continue
            threading.Thread(
                target=handle_client,
                args=(conn, addr, robot),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server_socket.close()
        robot.shutdown()
        print("Server stopped correctly.")


if __name__ == "__main__":
    main()
