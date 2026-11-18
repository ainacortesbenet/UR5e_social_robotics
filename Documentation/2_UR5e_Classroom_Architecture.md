# UR5e classroom architecture

The Student PCs are clients. They request social movements over the classroom
network. The Teacher PC runs the motion service and has the Ethernet connection
to the UR5e. The instructor supervises execution.

## Classroom network

```text
Student PC 1 ─┐
Student PC 2 ─┼── classroom network ── Teacher PC ── Ethernet ── UR5e
Student PC 3 ─┤
Student PC 4 ─┘
```

The Teacher PC has two network interfaces.

| Device | Network | Address |
|---|---|---|
| Teacher PC | Classroom LAN | `192.168.1.5/24` |
| Teacher PC | Robot Ethernet | `192.168.0.10/24` |
| UR5e | Robot Ethernet | `192.168.0.20/24` |
| Student PCs 1–4 | Classroom LAN | `192.168.1.15/24`, `192.168.1.25/24`, `192.168.1.35/24`, `192.168.1.45/24` |

## How each session uses the network

| Session | Student request | Teacher execution |
|---|---|---|
| [Python sockets](3a_Python_Sockets_Session.md) | Send the complete YAML over TCP port `5000` and receive `OK` or `ERROR`. | Simulate in RoboDK or send URScript to the robot on TCP port `30002`. |
| [ROS 2](4a_ROS2_Session.md) | Publish the motion name on `/social_behavior`. The Behavior Manager calls `/ur5e/run_sequence`. | Load the copied YAML and run it with MoveIt 2 and the UR driver. |

For ROS 2, match the Teacher's `ROS_DOMAIN_ID` to the selected Student PC
(group 1–4). DDS uses domain-dependent UDP ports. A domain groups discovery,
and access to real-robot control is reserved for the Teacher PC.

## Shared testing procedure

Verify these motions in this order:

1. `handshake`;
2. `give5`;
3. the new motion prepared at home (`<motion_name>`).

First run the three motions in simulation. Then run them on the real UR5e in the same order.

Before a real test, the instructor reviews every pose and trajectory for
workspace, collision and joint-limit risks. Confirm the TCP and payload, keep
the workspace clear and the emergency stop accessible, and run at reduced
speed with instructor approval. Stop if the real motion differs from simulation.

For each motion, record the simulation result, the real-robot result, any
error or protective stop, and the main difference between the two executions.
