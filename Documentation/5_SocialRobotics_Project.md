# Social Robotics Project with the UR5e

## Project objective

Design one safe and understandable social motion, such as waving, greeting, giving five or pointing, and implement it with two architectures:

1. Python sockets, RoboDK and URScript;
2. ROS 2, inverse kinematics and the UR controller.

Use equivalent poses in both implementations so that their communication and execution can be compared.

## Recommended reading order

Before starting the practical sessions:

1. read [Python sockets architecture](3_Python_Sockets_Architecture.md);
2. read [ROS 2 architecture](4_ROS2_Architecture.md);
3. review the sessions, responsibilities and deliverables in this document.

During each session, follow its practical guide step by step:

- **Session 1:** [Python sockets execution guide](../Python_sockets_Robotic_project/1_Instructions_python_SocialRobotics_Project.md)
- **Session 2:** [ROS 2 execution guide](../src/1_Instructions_ros2_SocialRobotics_Project.md)

The architecture documents explain **what the system contains and how it works**. The practical guides explain **which commands to execute and in which order**.

## Project overview

| Session | Architecture | Student request | Robot execution |
|---|---|---|---|
| 1 | Python sockets | Complete YAML over TCP | RoboDK and/or URScript |
| 2 | ROS 2 | Behavior name through a topic and service | IK and ROS 2 trajectory controller |

Both architectures keep direct robot access on the Teacher PC and allow different user interfaces to request the same high-level behavior.

## Before the laboratory

1. Choose the social meaning of the motion.
2. Define safe initial, intermediate and final poses.
3. Implement and validate the Python YAML with RoboDK.
4. Implement and validate the ROS 2 YAML with fake hardware.
5. Keep velocities conservative and movements easy to understand.
6. Record any differences between the two implementations.

No motion may be tested on the real UR5e before successful simulation and instructor approval.

## Session 1 — Python sockets

The student creates and registers a YAML behavior, sends it to the Teacher PC through TCP and observes its execution and response.

The main concepts are:

- custom client-server communication;
- complete YAML transfer;
- centralised validation and exclusive robot access;
- conversion from YAML to RoboDK commands or URScript;
- optional CLI, voice and face-and-voice inputs.

Expected result: the motion completes successfully in RoboDK and, after approval, on the real robot.

## Session 2 — ROS 2

The student implements the equivalent YAML sequence in the ROS 2 workspace. The Student PC sends only the behavior name; the Teacher PC loads the installed YAML and executes it through ROS 2 services and controllers.

The main concepts are:

- ROS 2 nodes, topics, services and actions;
- standard discovery and inspection;
- separation between command input and sequence execution;
- inverse kinematics through MoveIt 2;
- fake-hardware validation before real execution.

Expected result: the motion completes with fake hardware and, after approval, on the real UR5e.

## Responsibilities

### Student

- design and document the motion;
- create both YAML implementations;
- validate every pose in simulation;
- follow the practical guides in order;
- collect execution evidence and compare the architectures.

### Teacher PC

- provide the supervised connection to the UR5e;
- run the server, driver and robot-control components;
- contain the approved ROS 2 YAML;
- reject invalid or concurrent requests.

### Instructor

- review the simulated motion;
- verify the robot configuration and clear workspace;
- authorise and supervise real-robot execution.

## Safety principles

- Test every motion completely in simulation first.
- Start with conservative movement parameters and reduced robot speed.
- Check the TCP, payload and work area before real execution.
- Keep the emergency stop accessible.
- Stop immediately if the physical motion differs from the approved test.
- Do not treat voice or face recognition as a safety mechanism.

The practical guides contain the detailed safety and execution checklists.

## Deliverables

1. Python sockets YAML file.
2. ROS 2 YAML file.
3. Short description of the social meaning and selected poses.
4. Evidence of successful simulation in both architectures.
5. Evidence of supervised real-robot execution, when authorised.
6. Brief comparison of the two architectures.

The comparison should explain:

- what the Student PC sends in each architecture;
- where the YAML is stored;
- how the Teacher PC controls access to the robot;
- how errors and results are communicated;
- what ROS 2 provides compared with the custom TCP protocol.
