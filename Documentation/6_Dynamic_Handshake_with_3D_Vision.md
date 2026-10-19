# Dynamic handshake with Gemini2 and YOLO Pose

## Objective

The person silently offers a hand to the UR5e. The Gemini2 camera provides RGB
and depth images, YOLO Pose locates the body joints, and the robot moves towards
the measured wrist to perform a short handshake.

The example uses four simple layers:

```text
Gemini2 -> social_robot_perception -> social_robot_hri
         -> social_robot_behaviors -> ur5e_motion_server -> UR5e
```

- `/person_pose_3d` contains the 17 COCO body keypoints in metres.
- `/wrist_pose` contains the selected wrist pose.
- `/social_intent` publishes `handshake_offer` after several matching frames.
- `interaction_manager_node` calls `/ur5e/run_pose` for approach, contact,
  shake, retreat, and home poses.

The fixed YAML motions are stored in `social_robot_behaviors/motions`. The
camera-driven `handshake_dynamic` is implemented by the interaction manager and
does not generate a YAML file.

## 1. Install and build

Install the Gemini2 first if necessary: [Gemini2 installation](Files/Gemini2_installation.md).

YOLO Pose requires Ultralytics:

```bash
python3 -m pip install --user ultralytics
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

The first execution downloads `yolo11n-pose.pt` if it is not already present.

## 2. Calibrate the camera frame

The wrist is measured in the camera optical frame, but the robot receives poses
in the `table` frame. Measure the fixed camera pose and publish it with TF2.
Replace the six `<...>` values below with the calibrated translation in metres
and rotation in radians.

Terminal 1:

```bash
ros2 run tf2_ros static_transform_publisher \
  --x "<camera_x_m>" --y "<camera_y_m>" --z "<camera_z_m>" \
  --roll "<camera_roll>" --pitch "<camera_pitch>" --yaw "<camera_yaw>" \
  --frame-id table --child-frame-id camera_color_optical_frame
```

The child frame must match the frame printed by:

```bash
ros2 topic echo /camera/color/camera_info --once
```

Do not command the real robot until this transform has been measured and
checked in RViz.

## 3. Run the demonstration

Open separate terminals and source the workspace in each one:

```bash
source /opt/ros/humble/setup.bash
source ~/UR5e_social_robotics/install/setup.bash
```

Terminal 2 — start the Gemini2:

```bash
ros2 launch orbbec_camera gemini2.launch.py \
  color_width:=640 color_height:=480 color_fps:=15 \
  depth_width:=640 depth_height:=400 depth_fps:=15 \
  depth_registration:=true enable_point_cloud:=false enable_ir:=false
```

Terminal 3 — start a fake UR5e:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=true launch_rviz:=false
```

Terminal 4 — start MoveIt:

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

Terminal 5 — start the pose service:

```bash
ros2 run ur5e_motion_server ur5e_pose_server
```

Terminal 6 — start perception, gesture interpretation, and interaction
management in planning-only mode:

```bash
ros2 launch social_robot_behaviors dynamic_handshake.launch.py execute:=false
```

Terminal 7 — inspect the result:

```bash
ros2 topic echo /wrist_pose
```

In another terminal, check the detected intent:

```bash
ros2 topic echo /social_intent
```

## 4. Person action

1. Stand in front of the table, facing the robot and visible to the camera.
2. Keep the right shoulder, elbow, and wrist visible.
3. Extend the right arm naturally towards the robot as if offering a handshake.
4. Hold the pose briefly without speaking.
5. Wait until `/social_intent` prints `handshake_offer`.
6. Move away before repeating the gesture.

The thresholds and selected hand can be changed in
`social_robot_hri/config/gesture_interpreter_params.yaml`.

## 5. Real-robot execution

First verify all target coordinates with `execute:=false`. Check the tool,
payload, speed, workspace, camera transform, and emergency stop with the
instructor. Replace the fake driver in Terminal 3 with the real driver:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 launch_rviz:=false
```

Start the External Control program on the UR5e teach pendant. Then enable the
dynamic interaction:

```bash
ros2 launch social_robot_behaviors dynamic_handshake.launch.py execute:=true
```

The initial limits and speed are deliberately conservative and are configured
in `social_robot_behaviors/config/interaction_manager_params.yaml`. Vision is
not a safety system; all real-robot tests require supervision.
