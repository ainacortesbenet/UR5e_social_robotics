# UR5e setup environment

This document summarizes the necessary steps to work with UR based projecs:
- in virtual environment
- in a real UR5e robot arm

References:
- [UR5e Driver](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/humble)

## 1. UR5e Robot setup in a virtual environment

In simulation environment you have to install the complete UR metapackage:
````bash
sudo apt install ros-humble-ur
````
This metapackage installs:
- ur_robot_driver
- ur_moveit_config
- ur_description
- controllers and related configs

Verify the `.bashrc` file:
````bash
source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
source /home/user/UR5e_social_robotics/install/setup.bash
cd /home/user/UR5e_social_robotics
```` 
To sync you have to:
````bash
git add .
git commit -m "Message"
git push
````
First time you will have to add:
````bash
git config --global user.email "manel.puig@ub.edu"
git config --global user.name "manelpuig"
````

## 2. Real UR5e Robot setup environment

To connect a **real Universal Robots UR5e** to a **PC running Ubuntu 22.04 + ROS 2 Humble** we have to:
- install the required URCaps, 
- configure networking, and 
- control the robot using **ur_robot driver and MoveIt**.

### 2.1. Network Setup

Ensure the PC and UR5e are connected with a proper Ethernet cable.

Configure proper fixed IP addresses:
- PC IP: `192.168.0.10`
- UR5e IP: `192.168.0.20`

Verify connection in a pc-cmd:
```bash
ping 192.168.0.20
```

### 2.2. UR5e robot Configuration

There are requirements for the Polyscope software version and the URCap External Control.

#### 2.2.1. Polyscope software
To properly work on ros2 Humble, the Polyscope version has to be higher than 5.9.5. We have installed the 5.25.1 version.

The file we have to download is: https://www.universal-robots.com/download/software-ur-series/update/latest-polyscope-software-update-sw-5251-ur-series-e-series/

#### 2.2.2. URCap externalcontrol installation
Download:
```
externalcontrol-1.0.urcap
```
From:
https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/humble/ur_robot_driver/resources

**Install using Teach Pendant**
- Copy `.urcap` file to USB (FAT32)
- On the teach pendant:
   - **Settings → System → URCaps → Manage**
   - **Add** the file from USB  
- Reboot the controller when prompted.

**Configuration**

The configuration is based on the PC IP the robot has to connect to. 
- We specify it on `Installation` menu:
    ```
    Installation → URCaps → External Control
    ```

- Set:
    - **Control PC IP:** (e.g., `192.168.0.10`)
    - **Port:** `50002`

#### 2.2.3. ROS2 External Control Program
We first create a new program `ROS2_External_Control_PC_professor.urp` including only the `External Control` instruction configured before

Suggested Lab procedure:
- Create one Installation file (ROS2_PC_professor.installation)
- Include all the settings: gripper payload, gripper TCP, safety planes, etc.

### 2.3. PC Configuration

The PC is an Ubuntu22 with ROS2 Humble and we have to install different modulus:
````bash
sudo apt install ros-humble-ur-robot-driver
sudo apt install ros-humble-ros2controlcli
sudo apt install ros-humble-ur-calibration
sudo apt install ros-humble-moveit
````

The recommended installation is:
- Install needed packages:
    ````bash
    sudo apt update
    sudo apt install ros-humble-ur ros-humble-ros2controlcli
    ````
    - Extract the calibration data and obtain a correct URDF model from your real UR5e
    ````bash
    ros2 launch ur_calibration calibration_correction.launch.py \
        robot_ip:=192.168.0.20 \
        target_filename:=${HOME}/ur5e_calibration.yaml
    ````

### 2.3.1. Optional low-latency configuration

The low-latency kernel is relevant to the Teacher PC that runs the UR driver, controllers, and MoveIt 2. It is not required on Student PCs that only publish high-level requests.

Install and verify it with:

```bash
sudo apt install linux-lowlatency
sudo reboot
uname -r
```

For systems that require real-time scheduling permissions, configure them on the Teacher PC:

```bash
sudo groupadd realtime
sudo usermod -aG realtime $USER
sudo nano /etc/security/limits.d/99-realtime.conf
```

Add:

```text
@realtime soft rtprio 99
@realtime hard rtprio 99
@realtime soft priority 99
@realtime hard priority 99
@realtime soft memlock unlimited
@realtime hard memlock unlimited
```

Log out and back in, or reboot, after changing group membership.

### 2.4. Quick start

To properly start working on the UR5e with ROS2 Humble we have to:
- First on PC:
    - Source ROS:
        ```bash
        source /opt/ros/humble/setup.bash
        source ~/UR5e_social_robotics/install/setup.bash
        ```
    - Run the UR driver:
        ```bash
        ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e robot_ip:=192.168.0.20 launch_rviz:=false
        ```
- Now on `Teach Pendant`:
    - Load program: **ROS2_External_Control_PC_professor.urp**
    - Press **Play**  

### 2.5. Verify Joint States and run a first movement

- Open a new terminal and type:
    ```bash
    ros2 topic list
    ros2 topic echo /joint_states
    ```
- If messages stream → good connection.
- The good topic to publish a new target joint is: `/scaled_joint_trajectory_controller/joint_trajectory`
- Publish in a new terminal a target joint positions very close to the actual joint positions:
    ````bash
    ros2 topic pub --once /scaled_joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{
        joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        points: [
            {
            positions: [0.35, -2.3987, 2.5271, -3.2593, -0.5174, 3.1289],
            time_from_start: {sec: 4, nanosec: 0}
            }
        ]
    }"
    ````
- Publish in a new terminal a target joint positions to come back to the previous joint positions:
    ````bash
    ros2 topic pub --once /scaled_joint_trajectory_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory "{
        joint_names: ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'],
        points: [
            {
            positions: [0.5149, -2.3987, 2.5271, -3.2593, -0.5174, 3.1289],
            time_from_start: {sec: 4, nanosec: 0}
            }
        ]
    }"
    ````

## 3. OnRobot 2FG7 gripper control

OnRobot has launched a new driver to control his grippers with ROS2:

- [OnRobot webpage announcement](https://onrobot.com/es/physical-ai/physical-ai-developer-resources?utm_source=email&utm_medium=trigger_based&utm_campaign=physical-ai)
- [OnRobot-ros2](https://github.com/OnRobot/onrobot-ros2/tree/main)