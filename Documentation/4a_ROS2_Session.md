# Session 2 · ROS 2

Use the [ROS 2 setup guide](Files/References/UR5e_ROS2_Setup.md) to prepare the
environment. Complete the [local fake-hardware simulation](1_Project_Presentation.md#session-2---ubuntu-2204-vs-code-and-ros-2-humble)
before working with both PCs in the [classroom](2_UR5e_Classroom_Architecture.md).

## Define your social movement

Copy `handshake.yaml` from [the example motions](../src/social_robot_behaviors/motions/)
to `src/social_robot_behaviors/motions/<motion_name>.yaml`. Use a lowercase name
without spaces. ROS 2 looks up the filename using the requested motion name,
without the `.yaml` extension.

A motion file has a `common` settings block and an ordered `steps` list. This
single-step example uses the opening pose from `handshake.yaml`.

```yaml
common:
  execute: true
  group_name: ur_manipulator
  ik_link: tool0
  target_frame: table
  planning_frame: base_link
  max_velocity: 0.1
  max_acceleration: 0.1
  ik_timeout_sec: 1.0
  print_joints: true

steps:
  - name: home_start
    target_xyz: [0, -400, 500]
    target_rpy: [90.0, 0.0, 0.0]
    seed_from_joint_states: false
    seed_joints: [-60, -60, -100, 170, -60, 0]
    duration: 4.0
    sleep_after: 1.0
```

- `target_xyz` is the position in millimetres in `target_frame`, normally `table`.
- `target_rpy` is roll, pitch and yaw in degrees.
- `duration` is the movement time in seconds. Optional `sleep_after` is the pause in seconds.
- `seed_from_joint_states: true` uses the current joint state as the starting point for inverse kinematics. When supplying `seed_joints`, give six joint angles in degrees.

Add the intermediate and final poses under `steps`. Keep the start and end
configurations safe and verify each step in simulation. Follow the local
simulation guide to make the YAML available in your local install space. In the
lab, copy it into the Teacher's install space using step 2 below.

## 1. Configure ROS 2 multicast

Set `ROS_DOMAIN_ID` to the selected Student group number (1–4) on both
PCs. See the [classroom IP table](2_UR5e_Classroom_Architecture.md#classroom-network)
for Student and Teacher addresses.

### Student PC `~/.bashrc`

Add this block. Change `1` to `2`, `3` or `4` for the other groups:

```bash
source /opt/ros/humble/setup.bash
if [ -f "$HOME/UR5e_social_robotics/install/setup.bash" ]; then
    source "$HOME/UR5e_social_robotics/install/setup.bash"
fi
export ROS_DOMAIN_ID=1
export ROS_LOCALHOST_ONLY=0
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
unset CYCLONEDDS_URI
```

### Teacher container

Start the Humble container following the [Docker guide](Files/Docker/UB_Custom_Docker_container_ur5e.md).
Check the host repository path in `docker-compose.yaml` and enable X11 on the
Teacher host using that guide. Compose sets Cyclone DDS and classroom discovery.
Its Cyclone DDS XML selects the classroom interface `192.168.1.5`.

After choosing the group, stop the ROS daemon and set the matching domain in
each Teacher terminal you open for the session:

```bash
ros2 daemon stop
export ROS_DOMAIN_ID=1  # replace 1 with the selected Student group
```

On the Student PC, reload with `source ~/.bashrc` and run `ros2 daemon stop`.
On both PCs, check `ROS_DOMAIN_ID`, `ROS_LOCALHOST_ONLY` and
`RMW_IMPLEMENTATION` before launching any nodes.

## 2. Send `<motion_name>.yaml` to the Teacher PC

On the Student PC, open:

```bash
nano ~/UR5e_social_robotics/Documentation/Files/Send_motion/send_social_motion.py
```

The default parameters are prepared for the laboratory. Check `PROFESSOR_IP`, `PROFESSOR_USER`, `LOCAL_FOLDER` and `REMOTE_FOLDER` before running it. `REMOTE_FOLDER` must point to the Teacher `install/social_robot_behaviors/share/social_robot_behaviors/motions/` directory.

Run the copy tool:

```bash
cd ~/UR5e_social_robotics/Documentation/Files/Send_motion
python3 send_social_motion.py
```

When asked for the filename, enter:

```text
<motion_name>.yaml
```

The script copies the YAML directly to the Teacher `install` directory. No build is required. Continue only after it prints `Fitxer copiat correctament.`

## 3. Simulation with fake hardware

### Teacher PC - start first

Open three terminals inside the Teacher container. Check that all use the selected group domain.

Teacher terminal 1:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=true launch_rviz:=false
```

Teacher terminal 2:

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

Teacher terminal 3:

```bash
ros2 run ur5e_motion_server ur5e_sequence_server
```

Check that the server shows the installed directory containing `<motion_name>.yaml`.

### Student PC - start second

Student terminal 1:

```bash
ros2 launch social_robot_behaviors social_behavior.launch.py
```

Student terminal 2: send one motion at a time:

```bash
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'handshake'}"
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: 'give5'}"
ros2 topic pub --once /social_behavior std_msgs/msg/String \
  "{data: '<motion_name>'}"
```

Check that every IK request and trajectory succeeds in RViz. Stop all fake-hardware nodes before the real test.

## 4. Real UR5e

After reviewing the simulation with the instructor, stop the fake-hardware
nodes. On the Teacher PC, check the robot connection with `ping -c 4 192.168.0.20`.
Restart the driver in the first Teacher terminal using the simulation command
with `use_fake_hardware:=false`, then start the teach pendant program containing
**External Control**. Start MoveIt 2 and the sequence server as in simulation.

With instructor approval, repeat the Student PC steps and send the three motion
names in the same order. Record the results using the
[classroom testing procedure](2_UR5e_Classroom_Architecture.md#shared-testing-procedure).

## Check ROS 2 communication

Use a separate sourced terminal when troubleshooting:

```bash
ros2 node list
ros2 topic info /social_behavior --verbose
ros2 service type /ur5e/run_sequence
ros2 interface show ur5e_interfaces/srv/RunSequence
```

Continue with [face and voice HRI in ROS 2](4b_Face_and_Voice_HRI_ROS2_Demo.md).
