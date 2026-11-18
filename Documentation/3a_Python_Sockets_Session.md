# Session 1 · Python sockets

Complete the [local RoboDK simulation](1_Project_Presentation.md#session-1---windows-vs-code-python-sockets-and-robodk)
before following the [classroom testing procedure](2_UR5e_Classroom_Architecture.md#shared-testing-procedure).

## Define your movement

Copy an existing file from [motions](../Python_sockets_Robotic_project/motions/).
Set `sequence_name` and edit the ordered `steps` list. This example shows both
types of movement in one file.

```yaml
sequence_name: wave
steps:
  - name: initial_pose
    motion: moveJ
    joints_deg: [0, -90, 90, -90, -90, 0]
    acceleration: 0.5
    velocity: 0.1
  - name: greeting_pose
    motion: moveL
    target_xyz_mm: [-300, -300, 300]
    target_rpy_deg: [90, 0, 0]
    acceleration: 0.5
    velocity: 0.1
```

- `moveJ` targets six joint angles. The controller converts degrees to radians
  for URScript `movej(...)` or simulates the target with RoboDK `MoveJ()`.
- `moveL` moves the tool in a straight line to a Cartesian pose. For URScript
  `movel(...)`, the controller converts XYZ from millimetres to metres and
  roll, pitch and yaw from degrees to a rotation vector. RoboDK uses `MoveL()`.

Use the supplied motions as templates for a safe start and finish. Simulate
all intermediate steps before requesting a real test.

## 1. Prepare the Student PC

Save your YAML here and register it before the local simulation:

```text
Python_sockets_Robotic_project/motions/<motion_name>.yaml
```

Register it in `MOTIONS` in `behavior_manager_client.py`:

```python
MOTIONS = {
    "init": "motions/init.yaml",
    "handshake": "motions/handshake.yaml",
    "give5": "motions/give5.yaml",
    "<motion_name>": "motions/<motion_name>.yaml",
}
```

For the laboratory, set the Teacher address in the Student PC `config.py`:

```python
SERVER_IP = "192.168.1.5"
SERVER_PORT = 5000
```

## 2. Simulation

### Teacher PC - start first

In the Teacher PC `config.py`, set:

```python
EXECUTION_MODE = "simulation_only"
```

Start the server:

```powershell
cd UR5e_social_robotics\Python_sockets_Robotic_project
python ur5e_motion_server.py
```

Keep this terminal running. RoboDK must open and the server must listen on `0.0.0.0:5000`.

### Student PC - start second

Check the connection and the registered motions:

```powershell
Test-NetConnection 192.168.1.5 -Port 5000
cd UR5e_social_robotics\Python_sockets_Robotic_project
python motion_client.py --list
```

Send one motion at a time and wait for `OK: sequence executed`:

```powershell
python motion_client.py handshake
python motion_client.py give5
python motion_client.py <motion_name>
```

Check every movement in RoboDK. Stop the Teacher server after the three tests.

## 3. Real UR5e

### Teacher PC - start first

Check the robot connection:

```powershell
Test-NetConnection 192.168.0.20 -Port 30002
```

In the Teacher PC `config.py`, set:

```python
EXECUTION_MODE = "simulation_and_real"
```

Start the server again:

```powershell
cd UR5e_social_robotics\Python_sockets_Robotic_project
python ur5e_motion_server.py
```

### Student PC - repeat the three requests

With instructor approval, repeat the simulation commands in the same order.
Record the results as described in the [classroom guide](2_UR5e_Classroom_Architecture.md#shared-testing-procedure).

Continue with [face and voice using Python sockets](3b_Face_and_Voice_Python_Sockets.md).
