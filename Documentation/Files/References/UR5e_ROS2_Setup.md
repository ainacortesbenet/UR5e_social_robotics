# UR5e setup ROS2 environment

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

### 1.1. Python environment for voice, face and vision

On an Ubuntu 22.04 host, ROS 2 Humble uses the system Python 3.10. Keep ROS
packages installed with `apt`, and install the additional Python packages in a
virtual environment named `.venv-humble` at the repository root.

Install the native dependencies once:

```bash
sudo apt update
sudo apt install python3-venv python3-dev build-essential cmake \
    portaudio19-dev espeak-ng
```

Create the environment with the Ubuntu 22.04 interpreter. Use
`--system-site-packages` so that programs in the environment can also import
ROS packages such as `rclpy`, which were installed with `apt`:

```bash
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash

/usr/bin/python3 --version       # expected: Python 3.10.x
/usr/bin/python3 -m venv --system-site-packages .venv-humble
touch .venv-humble/COLCON_IGNORE

source .venv-humble/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install "setuptools==79.0.1"
```

Install the project dependencies. The face requirements already include the
voice requirements:

```bash
python -m pip install -r src/social_robot_hri/requirements_face.txt
python -m pip install openai python-dotenv pyttsx3
python -m pip install "SpeechRecognition[openai]"
python -m pip install ultralytics
```

Keep `setuptools==79.0.1`: the installed `colcon-core 0.21.1`
requires `setuptools<80`. Do not upgrade setuptools without checking
colcon compatibility.

Check dependency compatibility after installation:

```bash
python -m pip check
```

Ultralytics is only required by the vision exercises that use it. Verify the
environment after installation:

```bash
python -c "import rclpy; print('rclpy OK')"
python -c "import cv2, face_recognition, speech_recognition; print('HRI OK')"
python -c "import ultralytics; print('Ultralytics OK')"
```

#### Build with the virtual environment's Python

In a fresh terminal, build from the repository root using the virtual
environment's Python explicitly. Activating the environment alone does
not change the interpreter used by `/usr/bin/colcon`.

```bash
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash
source .venv-humble/bin/activate

.venv-humble/bin/python /usr/bin/colcon build \
    --symlink-install \
    --base-paths src

source install/setup.bash
```

Use this command for subsequent builds too. `--base-paths src` limits
package discovery to the source directory.

Existing Python packages built with the system interpreter must be
rebuilt using this command.

For the perception package, verify the generated executable:

```bash
head -n 1 install/social_robot_perception/lib/social_robot_perception/pose_3d_node
```

The interpreter on the first line must point inside `.venv-humble`.

#### Prepare each terminal before running nodes

After the first successful build:

```bash
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash
source .venv-humble/bin/activate
source install/setup.bash
```

For direct execution or debugging in VS Code, select
`.venv-humble/bin/python` using **Python: Select Interpreter**.
This setting does not regenerate executables used by `ros2 run`
or `ros2 launch`.

`.venv-humble` is local to this installation and must not be committed or
copied to another computer. The Docker workflow uses the same environment name
and Python version, but creates its own environment inside the container.

Optional: add the following to `~/.bashrc` to prepare new terminals
automatically:

```bash
source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

source ~/UR5e_social_robotics/.venv-humble/bin/activate

if [ -f ~/UR5e_social_robotics/install/setup.bash ]; then
    source ~/UR5e_social_robotics/install/setup.bash
fi
```

Build commands must still be run from the repository root using
`.venv-humble/bin/python /usr/bin/colcon`.

To sync you have to:

````bash
git add .
git commit -m "Message"
git push
````

First time you will have to add:

````bash
git config --global user.email "student_name@alumne.ub.edu"
git config --global user.name "github_name"
````

## 2. Real UR5e Robot setup environment

To connect a **real Universal Robots UR5e** to a **PC running Ubuntu 22.04 + ROS 2 Humble** we have to:

- install the required URCaps,
- configure networking, and
- control the robot using **ur_robot driver and MoveIt**.

### 2.1. Network Setup

See [Classroom architecture](../../2_UR5e_Classroom_Architecture.md) for the common
network, IP assignments and Student domains `1`–`4`. The steps below configure
the dedicated Teacher PC–robot link. On an Ubuntu 24.04 Teacher host, run Humble
inside Docker following the [Docker guide](../Docker/UB_Custom_Docker_container_ur5e.md).

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
    source ~/UR5e_social_robotics/.venv-humble/bin/activate
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
