# UR5e Classroom Architecture

## Overview

This document defines the classroom architecture used to teach two ways of controlling a UR5e robot:

1. Python TCP sockets and URScript.
2. ROS 2 and MoveIt 2.

The robot is connected to a dedicated Teacher PC. Student PCs send high-level requests through the local network, while the Teacher PC validates and executes robot motions.

The same client-server idea is used in both stages. The communication technology and motion execution layer change, but the responsibility boundary remains the same.

## Classroom network

The classroom contains:

- one Ubuntu 22.04 Teacher PC connected to the UR5e through Ethernet;
- several Student PCs connected to the classroom LAN or WiFi;
- one UR5e robot controlled only by the Teacher PC.

```text
Student PC 1 ─┐
Student PC 2 ─┼── classroom network ── Teacher PC ── Ethernet ── UR5e
Student PC 3 ─┤
Student PC 4 ─┘
```

Only the Teacher PC runs the robot driver, MoveIt 2, trajectory controllers, and the motion execution server. Student PCs run clients or publishers that request prepared behaviors.

Use the actual network values configured for the laboratory. The examples below use placeholders:

```text
ROBOT_IP=<UR5E_IP>
TEACHER_PC_IP=<TEACHER_PC_IP>
STUDENT_PC_IP=<STUDENT_PC_IP>
```

## Teacher PC responsibilities

The Teacher PC is the central control and safety point. It:

- communicates directly with the UR5e;
- runs the UR driver and, for ROS 2, MoveIt 2;
- receives requests from student applications;
- validates behavior names, YAML files, poses, and motion parameters;
- prevents concurrent or unauthorized executions;
- supervises the first execution of every student motion;
- stops the experiment when a safety problem is detected.

Student PCs must not run the real robot driver, MoveIt 2, RTDE communication, or trajectory controllers for the classroom robot.

## Stage 1: Python sockets and URScript

The first stage introduces low-level industrial robot communication.

```text
Student application
        │ TCP socket
        ▼
Teacher PC: ur5e_motion_server.py
        ▼
ur5e_robot_controller.py
        │ URScript
        ▼
UR5e
```

The Student PC runs `motion_client.py` from `Python_sockets_Robotic_project/`. The client resolves a behavior name locally, validates the corresponding file, and sends the complete YAML sequence to the server. Optional voice and face interfaces select behavior names through the same communication layer.

The Teacher PC starts `ur5e_motion_server.py`, which imports `ur5e_robot_controller.py`. The server parses the received YAML, executes it through the controller, and permits only one motion at a time.

The Python motion format uses fields such as:

```yaml
sequence_name: wave

steps:
  - name: approach
    motion: moveL
    target_xyz_mm: [-300, -300, 300]
    target_rpy_deg: [90, 0, 0]
    velocity: 0.10
    acceleration: 0.50
    time: 3.0
    blend: 0.0
```

The client and server configuration uses TCP port `5000`. During local development, use `127.0.0.1`; in the classroom, the client uses the Teacher PC address and the server listens on `0.0.0.0`.

## Stage 2: ROS 2 and MoveIt 2

The second stage replaces the custom TCP protocol with ROS 2 communication and direct URScript execution with MoveIt 2 and the UR driver.

```text
Student command publisher
        │ /social_behavior
        ▼
Behavior Manager Client
        │ /ur5e/run_sequence
        ▼
UR5e Sequence Server
        ▼
MoveIt 2 and UR driver
        ▼
UR5e
```

The ROS 2 components are located in these packages:

```text
src/social_robot_behaviors/
src/ur5e_motion_server/
src/ur5e_motion_utils/ur5e_robot_controller/
src/ur5e_interfaces/
```

The Behavior Manager Client subscribes to `/social_behavior` and calls `/ur5e/run_sequence`. The request contains the logical behavior name, for example `handshake`. The sequence server resolves that name to `handshake.yaml` in the installed `ur5e_robot_controller/config/` directory.

To execute a sequence directly, use the launch file that exists in the `ur5e_robot_controller` package:

```bash
ros2 launch ur5e_robot_controller ur5e_pose_sequence.launch.py \
  sequence_file:=handshake.yaml
```

The ROS 2 motion format is different from the Python sockets format. The same poses can be reused, but the YAML file must be adapted to the selected controller.

## Common classroom workflow

1. Design a social motion in RoboDK or another offline tool.
2. Choose safe initial, intermediate, and final poses.
3. Create the YAML file in the format required by the selected stage.
4. Test the complete motion offline or with fake hardware.
5. Check the YAML structure, limits, timing, workspace, and collision risk.
6. Submit the motion to the instructor for review.
7. Transfer the validated file to the Teacher PC.
8. Run the first real-robot execution under instructor supervision.
9. Compare the simulated and real executions and record any difference.

## Fake hardware and home testing

ROS 2 motions must be tested with the fake UR5e before they are tested on the real robot:

```bash
cd ~/UR5e_social_robotics
colcon build --symlink-install
source install/setup.bash
```

Start the fake driver and MoveIt 2 in separate terminals:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e \
  robot_ip:=<UR5E_IP> \
  use_fake_hardware:=true \
  launch_rviz:=false
```

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e \
  launch_rviz:=true
```

Then test a sequence:

```bash
ros2 launch ur5e_robot_controller ur5e_pose_sequence.launch.py \
  sequence_file:=handshake.yaml
```

The IP argument is retained by the launch configuration, but fake hardware does not connect to a physical robot.

## Safety and instructor validation

Every motion must:

- have a clear social meaning;
- start and finish in a safe configuration;
- stay inside the robot workspace;
- avoid collisions and joint limits;
- use slow and smooth movements;
- use validated velocities, accelerations, durations, and blending;
- be tested with fake hardware or an offline simulator first.

Before a real execution, the instructor must:

1. review the YAML file and its poses;
2. verify the workspace, collision risk, speed, and acceleration;
3. confirm that the robot and teach pendant are correctly configured;
4. authorize the execution;
5. supervise the first execution at reduced speed.

During every experiment, the workspace must remain clear, the emergency stop must be accessible, and one person must be ready to stop the robot. An unverified YAML file must never be executed on the real robot.

## Educational progression

| Layer | Python sockets and URScript | ROS 2 and MoveIt 2 |
|---|---|---|
| Student side | Python client | ROS 2 publisher or client node |
| Teacher side | TCP motion server | Sequence server and ROS 2 nodes |
| Communication | TCP socket | ROS 2 topics and services |
| Motion description | Python sockets YAML | ROS 2 controller YAML |
| Robot execution | URScript | MoveIt 2 and UR driver |
| Safety point | Teacher-side validation | Teacher-side validation and supervised execution |

This progression introduces networking, modular software, ROS 2 nodes, services, MoveIt 2, robot drivers, TF, trajectory execution, and human-robot interaction without changing the central safety boundary.

## Related documents

- [UR5e setup](1_UR5e_setup.md): operating-system, driver, network, and robot setup.
- [Python sockets architecture](3_Python_Sockets_Architecture.md): components, TCP communication, YAML and URScript flow.
- [ROS 2 architecture](4_ROS2_Architecture.md): nodes, topics, services, actions and sequence execution.
- [Social robotics project](5_SocialRobotics_Project.md): sessions, responsibilities, safety and deliverables.
