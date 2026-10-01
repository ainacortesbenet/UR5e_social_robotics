## UB custom Docker-based ROS2 Humble UR5eenvironment

We have designed a University of Barcelona custom Docker-based ROS 2 Humble environment to simplify student access to ROS 2 and ensure platform-independent workflows in robotics courses.

## Create a Python virtual environment on the host

Before using the Docker container, create a Python virtual environment in the host project folder.

```bash
cd UR5e_social_robotics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ultralytics pyrealsense2
```

For Windows, use:

```powershell
cd C:\path\to\UR5e_social_robotics
py -3.10 -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install ultralytics pyrealsense2
```

Add the following lines to your shell startup file (`.bashrc` on Ubuntu/Linux):

```bash
source /opt/ros/humble/setup.bash
source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash
source /root/UR5e_social_robotics/install/setup.bash
cd /root/UR5e_social_robotics
```

Then reload it:

```bash
source ~/.bashrc
```

Do not commit the `.venv` folder to GitHub. Add it to `.gitignore`:

```gitignore
.venv/
venv/
__pycache__/
*.pyc
```

**PC-ubuntu/linux** Configure properly the `docker-compose.yaml`

- Open a terminal in `~/UR5e_social_robotics/Documentation/Files/Docker` and run:
    ````bash
    xhost +local:root            # only in case of Host Ubuntu to allow X11 for Docker 
    chmod +x entrypoint_pc.sh
    docker compose up
    ````
**PC-windows** Configure properly the `docker-compose.yaml`

- Open a terminal in `~/UR5e_social_robotics/Documentation/Files/Docker` and run:
    ````bash
    docker compose up
    ````

- In Host VScode you can `attach VScode`. You can also connect with container typing:
    ```bash
    docker exec -it pc_humble bash
    code .  # to open VSCode inside the container
    ```
- Clone your ws in `/root/`
- Verify in container **.bashrc** to have:
    ```bash
    # ROS 2 Humble
    source /opt/ros/humble/setup.bash
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

    # Project workspace
    source /root/UR5e_social_robotics/install/setup.bash

    # Python virtual environment for YOLO / Realsense
    source /root/UR5e_social_robotics/.venv/bin/activate

    cd /root/UR5e_social_robotics
    ```
You are ready to work inside the container and to connect to the robot hardware within ROS2 Humble on Docker!

- To stop the container, open a new terminal on Host in `~/UR5e_social_robotics/Documentation/Files/Docker` and run:
    ```bash
    docker compose down
    ```
- To see the Images and Containers:
    ```bash
    docker ps -a               # containers
    docker images              # images
    ```
- To modify the `Dockerfile`, build and push to Docker Hub, you can follow the instructions:
    ```bash
    docker build -t manelpuig/ros2-humble-ub-ur5e:latest .
    docker login
    docker push manelpuig/ros2-humble-ub-ur5e:latest
    ```
- Note that:
    - Dockerfile0: Base installation without 3D cameras
    - Dockerfile: Full installation with ORBBEC and Intel Realsense 3D Cameras

# 3D cameras

You will have to install Udev rules on Host once and then check that the cameras are properly detected in the container.
## Realsense D435

- install Udev rules on Host
    ````bash
    cd /tmp
    wget https://raw.githubusercontent.com/IntelRealSense/librealsense/master/config/99-realsense-libusb.rules
    sudo cp 99-realsense-libusb.rules /etc/udev/rules.d/
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    ````
- Important to add on `.bashrc` an environment variable on `Container`:
    ````bash
    export LD_PRELOAD=/usr/local/lib/librealsense2.so
    ````

- Verify that the camera is detected in the container
    ````bash
    lsusb
    rs-enumerate-devices
    ````
- Launch
    ````bash
    ros2 launch realsense2_camera rs_launch.py \
    rgb_camera.color_profile:=640x480x15 \
    depth_module.depth_profile:=640x360x15 \
    pointcloud.enable:=false
  ````

## Orbbec Gemini2

- install Udev rules on Host
````bash
git clone https://github.com/orbbec/OrbbecSDK_ROS2.git
cd OrbbecSDK_ROS2
sudo bash scripts/install_udev_rules.sh
````
- Verify that the camera is detected in the container
    ````bash
    lsusb
    ````
- Launch
    ````bash
    ros2 launch orbbec_camera gemini2.launch.py \
        color_width:=640 \
        color_height:=480 \
        color_fps:=15 \
        color_format:=MJPG \
        depth_width:=640 \
        depth_height:=400 \
        depth_fps:=15 \
        depth_registration:=false \
        enable_ir:=false \
        enable_point_cloud:=false \
        enable_accel:=false \
        enable_gyro:=false \
        connection_delay:=3000
    ````