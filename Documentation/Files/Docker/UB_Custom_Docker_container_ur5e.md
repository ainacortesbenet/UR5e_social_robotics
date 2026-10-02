## UB custom Docker-based ROS2 Humble UR5eenvironment

We have designed a University of Barcelona custom Docker-based ROS 2 Humble environment to simplify student access to ROS 2 and ensure platform-independent workflows in robotics courses.

## Python environment with an Ubuntu 24.04 host

In this scenario Ubuntu 24.04 is only the Docker host. ROS 2 nodes, voice and
face recognition, and Ultralytics always run inside the Ubuntu 22.04/ROS 2
Humble container.

The repository is bind-mounted by `docker-compose.yaml`:

```text
Host:      /home/biorob/Desktop/UR5e_social_robotics
Container: /root/UR5e_social_robotics
```

Therefore `.venv-humble` is stored on the host disk together with the
repository, but it must be created from inside the container. Do not create it
with the Ubuntu 24.04 host Python: the host normally uses Python 3.12, whereas
ROS 2 Humble uses Python 3.10. Environments containing binary packages such as
PyTorch, `dlib` or OpenCV are not portable between those Python versions.

Start the container after cloning the repository and configuring its absolute
bind-mount path in `docker-compose.yaml`:

```bash
cd ~/Desktop/UR5e_social_robotics/Documentation/Files/Docker
xhost +local:root # Host Ubuntu to allow X11 for Docker
chmod +x entrypoint_pc.sh
docker compose up -d
docker exec -it pc_humble_ur5e bash
```

Then create the environment **inside the container**:

```bash
source /opt/ros/humble/setup.bash
cd /root/UR5e_social_robotics
python3 --version                 # expected: Python 3.10.x
python3 -m venv --system-site-packages .venv-humble
source .venv-humble/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r src/social_robot_hri/requirements_face.txt
python -m pip install ultralytics
```

The face requirements already include the voice requirements. Ultralytics is
only required by the vision exercises that use it. Verify the installation:

```bash
python -c "import rclpy; print('rclpy OK')"
python -c "import cv2, face_recognition, speech_recognition; print('HRI OK')"
python -c "import ultralytics; print('Ultralytics OK')"
```

The environment is now also visible on the host at
`~/Desktop/UR5e_social_robotics/.venv-humble`, but it is for the container only:
never activate it on the Ubuntu 24.04 host. It persists across
`docker compose down` because it is in the bind-mounted repository. Do not move
the repository after creating it because virtual-environment scripts contain
absolute paths.

`.venv-humble/` is excluded by the repository `.gitignore`. Consequently,
Ultralytics and PyTorch are neither committed nor included in the Docker image.

## Create the Docker container from UB Docker Image

**PC-ubuntu/linux** Configure properly the `docker-compose.yaml`

- Open a terminal in `~/UR5e_social_robotics/Documentation/Files/Docker`:
- Verify the path: `/home/biorob/Desktop/UR5e_social_robotics` and modify it on docker-compose.yaml
- run:
    ````bash
    xhost +local:root # Host Ubuntu to allow X11 for Docker
    chmod +x entrypoint_pc.sh
    docker compose up
    ````
**PC-windows** Configure properly the `docker-compose.yaml`

- Open a terminal in `~/UR5e_social_robotics/Documentation/Files/Docker`:
- Verify the path: `/home/biorob/Desktop/UR5e_social_robotics` and modify it on docker-compose.yaml
- Change environment to `DISPLAY=host.docker.internal:0.0`
- run:
    ````bash
    docker compose up
    ````

In Host VScode you can `attach VScode`.

- You can also connect with container typing:
    ```bash
    docker exec -it pc_humble_ur5e bash
    code .  # to open VSCode inside the container
    ```
- The repository is mounted at `/root/UR5e_social_robotics`, and
  `.venv-humble` is stored inside that mounted repository.
- Verify in container **.bashrc** to have:
    ```bash
    # ROS 2 Humble
    source /opt/ros/humble/setup.bash
    source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash

    # Project workspace
    source /root/UR5e_social_robotics/install/setup.bash

    # Python virtual environment for ROS HRI and YOLO
    source /root/UR5e_social_robotics/.venv-humble/bin/activate

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
cd OrbbecSDK_ROS2/orbbec_camera
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
