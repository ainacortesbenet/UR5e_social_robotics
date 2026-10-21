# Orbbec Gemini2 setup

This short guide is for Ubuntu 22.04 with ROS 2 Humble. Skip it when the
Gemini2 driver is already installed.

## Install the driver

```bash
sudo apt update
sudo apt install -y ros-humble-orbbec-camera ros-humble-orbbec-description
```

Install the USB rule:

```bash
sudo cp /opt/ros/humble/share/orbbec_camera/udev/99-obsensor-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Unplug and reconnect the camera. Use a USB 3 port.

## Verify the camera

```bash
source /opt/ros/humble/setup.bash
lsusb
ros2 run orbbec_camera list_devices_node
```

The device list must contain `Orbbec Gemini2` and preferably `USB3.0`.

## Start registered RGB and depth images

```bash
ros2 launch orbbec_camera gemini2.launch.py \
  color_width:=640 color_height:=480 color_fps:=15 \
  depth_width:=640 depth_height:=400 depth_fps:=15 \
  depth_registration:=true \
  enable_point_cloud:=false \
  enable_ir:=false
```

Check the topics and their rates:

```bash
ros2 topic list | grep camera
ros2 topic hz /camera/color/image_raw
ros2 topic hz /camera/depth/image_raw
```

The dynamic-handshake example expects the default topics
`/camera/color/image_raw`, `/camera/depth/image_raw`, and
`/camera/color/camera_info`. Change
`social_robot_perception/config/pose_3d_params.yaml` if the driver uses other
names.

The complete Raspberry Pi and Ubuntu 24/Docker instructions are maintained in
`my_rUBot_mecanum/Documentation/Files/Install_robot/3Dcamera`.
