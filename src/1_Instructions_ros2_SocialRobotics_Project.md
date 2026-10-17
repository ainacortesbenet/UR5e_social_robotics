# Ubuntu execution — ROS 2 Social Robotics Project

## Purpose

This guide explains how to create and verify a social motion with ROS 2 Humble and MoveIt 2 in successive stages:

1. prepare the ROS 2 workspace and the motion YAML;
2. test the complete architecture with a fake UR5e;
3. repeat the test over the laboratory network;
4. execute the approved motion on the real UR5e;
5. optionally replace the terminal command with voice or face-and-voice interaction.

Complete the stages in order. A successful fake-hardware test and instructor approval are required before moving the real robot.

## Architecture

```text
Student PC                                      Teacher PC

terminal / voice / face + voice
              |
              | /social_behavior
              v
Behavior Manager Client
              |
              | /ur5e/run_sequence
              | RunSequence(sequence_name)
              +-------------------------------> UR5e Sequence Server
                                                         |
                                                         | loads <motion_name>.yaml
                                                         v
                                                MoveIt 2 + UR driver
                                                         |
                                                         +----> fake or real UR5e
              <------------------------------- success + message
```

The student sends only the motion name. The YAML file is installed on the computer that runs the sequence server. ROS 2 discovery replaces the custom IP-and-port protocol used by the Python sockets project.

## Project files used in this activity

- `src/ur5e_motion_utils/ur5e_robot_controller/config/<motion_name>.yaml`: motion sequence;
- `src/social_robot_behaviors/social_robot_behaviors/behavior_manager_client_node.py`: receives `/social_behavior` and requests the sequence;
- `src/ur5e_motion_server/ur5e_motion_server/ur5e_sequence_server.py`: validates the request and launches the sequence;
- `src/ur5e_motion_utils/ur5e_robot_controller/ur5e_robot_controller/ur5e_pose_sequence.py`: calculates IK and sends each trajectory;
- `src/social_robot_hri/`: optional voice and face-verification nodes.

## 1. Prepare the ROS 2 workspace

The supported environment is Ubuntu 22.04 with ROS 2 Humble. Install the ROS 2 packages once:

```bash
sudo apt update
sudo apt install ros-humble-ur ros-humble-ros2controlcli python3-colcon-common-extensions
```

Clone or open the repository and build it:

```bash
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

### 1.1 Configure `.bashrc` on the Teacher PC and Student PC

Configure both computers once so that every new terminal automatically loads ROS 2, this workspace and the shared DDS settings. On the **Teacher PC** and the **Student PC**, open `.bashrc`:

```bash
nano ~/.bashrc
```

Add these lines at the end of the file on both computers:

```bash
source /opt/ros/humble/setup.bash
source "$HOME/UR5e_social_robotics/install/setup.bash"
export ROS_DOMAIN_ID=0
export ROS_LOCALHOST_ONLY=0
```

Save with `Ctrl+O`, press `Enter`, and exit with `Ctrl+X`. Apply the configuration in the current terminal:

```bash
source ~/.bashrc
```

Verify it on both computers:

```bash
echo "$ROS_DISTRO"
echo "$ROS_DOMAIN_ID"
echo "$ROS_LOCALHOST_ONLY"
```

The expected values are `humble`, `0`, and `0`. From this point onward, the commands in this guide assume that `.bashrc` is configured correctly; the `source` and `export` commands are not repeated in every terminal.

See `Documentation/1_UR5e_setup.md` for the complete installation, real-robot and optional HRI environment setup.

## 2. Create and install your motion

Use a short lowercase name without spaces, for example `wave`. Copy an existing sequence:

```bash
cd ~/UR5e_social_robotics/src/ur5e_motion_utils/ur5e_robot_controller/config
cp handshake.yaml wave.yaml
```

Edit `wave.yaml`. A sequence contains a `common` section and a non-empty `steps` list. Each step needs:

- `target_xyz`: Cartesian position in millimetres;
- `target_rpy`: orientation in degrees;
- `duration`: movement time in seconds;
- optionally `sleep_after`, `seed_from_joint_states`, and `seed_joints`.

Use `init.yaml`, `handshake.yaml`, and `give5.yaml` as structural examples. Keep the initial and final poses safe, use conservative durations, and check every intermediate pose.

Build again so that the new YAML is available in the install space:

```bash
cd ~/UR5e_social_robotics
colcon build --symlink-install
source install/setup.bash
```

No Python registration is required. The requested behavior name must match the YAML filename without `.yaml`.

## 3. Verify locally with a fake UR5e

Open five Ubuntu terminals. Each terminal automatically loads the required environment through the `.bashrc` configured in section 1.1.

### 3.1 Start the fake UR5e driver

Terminal 1:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=true launch_rviz:=false
```

With fake hardware, no connection to the physical robot is made; the `robot_ip` value is still required by the launch file.

### 3.2 Start MoveIt 2 and RViz

Terminal 2:

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

Wait until the robot model appears and MoveIt 2 is ready.

### 3.3 Start the sequence server

Terminal 3:

```bash
ros2 run ur5e_motion_server ur5e_sequence_server
```

Expected evidence:

- the node reports `UR5e sequence server ready`;
- the service is `/ur5e/run_sequence`;
- the displayed sequence directory contains your YAML file.

### 3.4 Start the Behavior Manager Client

Terminal 4:

```bash
ros2 launch social_robot_behaviors social_behavior.launch.py
```

### 3.5 Send the motion command

Terminal 5:

```bash
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'wave'}"
```

Replace `wave` with your motion name. A successful test must show all of the following:

- the Behavior Manager receives the correct behavior name;
- the server finds the corresponding YAML;
- every IK request succeeds;
- every trajectory is accepted and completed;
- the complete motion is visible in RViz;
- the service response reports successful execution;
- the motion starts and ends in safe poses and is socially understandable.

If you change the YAML in the source directory, rebuild and source the workspace before testing it again. Stop the nodes with `Ctrl+C` when finished.

### 3.6 Inspect the ROS 2 communication

Use a separate sourced terminal when troubleshooting:

```bash
ros2 node list
ros2 topic info /social_behavior --verbose
ros2 service type /ur5e/run_sequence
ros2 interface show ur5e_interfaces/srv/RunSequence
```

## 4. Verify the distributed architecture in the laboratory

The Teacher PC runs the sequence server, MoveIt 2 and the robot driver. The Student PC runs the Behavior Manager and command interface.

Connect both computers to the classroom network. The `.bashrc` configured in section 1.1 ensures that both use the same ROS domain and allow communication with remote ROS 2 nodes.

The classroom network normally uses:

- Teacher PC: `192.168.1.5`;
- Student PC: the address assigned by the instructor, such as `192.168.1.15` for group 1.

Confirm the assigned addresses with the instructor. Check connectivity from the Student PC:

```bash
ping 192.168.1.5
```

First repeat the fake-hardware test:

1. on the Teacher PC, run terminals 1, 2 and 3 from section 3;
2. on the Student PC, run terminals 4 and 5;
3. confirm that `ros2 node list` on the Student PC shows the nodes running on the Teacher PC;
4. publish the motion and verify it in RViz on the Teacher PC.

If the computers can ping each other but ROS 2 nodes are not discovered, check that both use the same `ROS_DOMAIN_ID`, `ROS_LOCALHOST_ONLY=0`, and that the firewall or network does not block DDS discovery traffic.

## 5. Execute the approved motion on the real UR5e

Only the Teacher PC connects directly to the robot:

- Teacher PC robot-network address: `192.168.0.10`;
- UR5e address: `192.168.0.20`;
- Student PC continues communicating with the Teacher PC through the classroom network.

Before starting, confirm instructor approval, the correct TCP and payload, a clear workspace, reduced speed, and access to the emergency stop. On the Teacher PC, verify the robot connection:

```bash
ping 192.168.0.20
```

Copy the approved `<motion_name>.yaml` to the Teacher PC and build its workspace, or copy it directly to:

```text
~/UR5e_social_robotics/install/ur5e_robot_controller/share/ur5e_robot_controller/config/
```

The helper `Documentation/Files/Send_motion/send_social_motion.py` performs this copy with `scp`. On the Student PC, open the script:

```bash
nano ~/UR5e_social_robotics/Documentation/Files/Send_motion/send_social_motion.py
```

Verify these four parameters:

```python
PROFESSOR_IP = "192.168.1.5"
PROFESSOR_USER = "<teacher_username>"
LOCAL_FOLDER = "/home/<student_username>/UR5e_social_robotics/src/ur5e_motion_utils/ur5e_robot_controller/config/"
REMOTE_FOLDER = "/home/<teacher_username>/UR5e_social_robotics/install/ur5e_robot_controller/share/ur5e_robot_controller/config/"
```

- `PROFESSOR_IP`: Teacher PC address reachable from the Student PC; normally `192.168.1.5` on the classroom network;
- `PROFESSOR_USER`: login username on the Teacher PC;
- `LOCAL_FOLDER`: source directory containing the approved YAML on the Student PC;
- `REMOTE_FOLDER`: installed configuration directory used by `ur5e_sequence_server` on the Teacher PC.

Replace the placeholders with the actual usernames and confirm that both paths exist. Then run on the Student PC:

```bash
cd ~/UR5e_social_robotics/Documentation/Files/Send_motion
python3 send_social_motion.py
```

When prompted with `Nom del fitxer YAML:`, enter the complete filename, including the extension. For example:

```text
wave.yaml
```

Enter the Teacher PC password if `scp` requests it. A successful transfer prints `Fitxer copiat correctament.`

### 5.1 Teacher PC — terminal 1: real UR5e driver

```bash
cd ~/UR5e_social_robotics
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=false launch_rviz:=false
```

Keep this terminal running. On the UR5e teach pendant, load the program containing **External Control** and press **Play**.

### 5.2 Teacher PC — terminal 2: MoveIt 2 and RViz

Open a new terminal on the Teacher PC:

```bash
cd ~/UR5e_social_robotics
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

Wait until the robot model appears and MoveIt 2 is ready. Keep this terminal running.

### 5.3 Teacher PC — terminal 3: sequence server

Open another terminal on the Teacher PC:

```bash
cd ~/UR5e_social_robotics
ros2 run ur5e_motion_server ur5e_sequence_server
```

Confirm that the server reports `UR5e sequence server ready` and shows the directory containing the approved YAML. Keep this terminal running.

### 5.4 Student PC — terminal 4: Behavior Manager Client

Open a terminal on the Student PC:

```bash
cd ~/UR5e_social_robotics
ros2 launch social_robot_behaviors social_behavior.launch.py
```

Keep this terminal running. It must report that the Behavior Manager has started and is waiting for `/ur5e/run_sequence`.

### 5.5 Student PC — terminal 5: send the approved motion

Open another terminal on the Student PC:

```bash
cd ~/UR5e_social_robotics
ros2 service list | grep /ur5e/run_sequence
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: '<motion_name>'}"
```

Replace `<motion_name>` with the approved YAML filename without `.yaml`. For example, to execute `wave.yaml`:

```bash
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'wave'}"
```

The server accepts one sequence at a time. Stop immediately with the robot emergency-stop or protective-stop procedure if the real trajectory differs from the approved test.

## 6. Optional voice commands

Voice replaces the terminal publisher and still produces the same `/social_behavior` message. Install the optional dependencies on the Student PC using the environment described in `Documentation/1_UR5e_setup.md`, then launch:

```bash
ros2 launch social_robot_hri social_robot_hri.launch.py
```

Test the interpreter without a microphone or robot first:

```bash
ros2 run social_robot_hri voice_interpreter_node
```

In terminal 2, inspect the interpreted output:

```bash
ros2 topic echo /social_behavior
```

In terminal 3, publish a synthetic voice message:

```bash
ros2 topic pub --once /voice/text std_msgs/msg/String \
  "{data: 'robot handshake'}"
```

The interpreted message must contain exactly one valid motion name. Then test the microphone with fake hardware before using the real robot. Internet access is required by the Google speech-recognition service.

## 7. Optional face verification before voice control

Face verification is a one-time access gate for voice commands. Use a clear frontal reference photograph and launch it on the Student PC with an absolute image path:

```bash
ros2 launch social_robot_hri face_voice_hri.launch.py \
  reference_image:=/home/student/authorised_user.jpg \
  camera_index:=0
```

Before connecting the Behavior Manager or robot, verify with `ros2 topic echo /social_behavior` that:

- the authorised face allows `robot <motion_name>` to publish the expected motion;
- a non-matching face, missing image or unavailable camera publishes no motion.

Repeat the complete chain with fake hardware. Face matching is a classroom demonstration, not secure biometric authentication or a robot safety system.

## Final safety checklist

Before a real execution, confirm:

- [ ] the YAML was tested completely with fake hardware;
- [ ] all IK and trajectory steps completed without errors;
- [ ] initial, intermediate and final poses are safe;
- [ ] the installed YAML on the Teacher PC is the approved version;
- [ ] TCP, payload and External Control are configured correctly;
- [ ] the workspace is clear and robot speed is reduced;
- [ ] the instructor is supervising and the emergency stop is accessible.
