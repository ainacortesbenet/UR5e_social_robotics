# Handshake approach with Gemini2 and YOLO Pose

## Objective

The person silently offers a hand to the UR5e. The Gemini2 camera provides RGB
and depth images, YOLO Pose locates the body joints, and the robot moves the
TCP towards the measured wrist before performing a short handshake sequence.

This first implementation is intentionally a **wrist snapshot**, not hand
tracking: when the offer gesture is detected, it captures one valid wrist pose,
transforms it into the robot `table` frame, and uses that fixed point for the
approach, contact, shake and retreat motions. The wrist is not followed while
the robot is moving.

The example uses four simple layers:

```text
Gemini2 -> social_robot_perception -> social_robot_hri
         -> social_robot_behaviors -> ur5e_motion_server -> UR5e
```

- `/person_pose_3d` contains the 17 COCO body keypoints in metres.
- `/wrist_pose` contains the selected wrist pose in the Gemini2 optical frame.
- `/handshake_target` contains the captured wrist pose transformed to `table`.
- `/social_intent` publishes `handshake_offer` after several matching frames.
- `interaction_manager_node` calls `/ur5e/run_pose` for approach, contact,
  shake, retreat, and home poses.

The fixed YAML motions are stored in `social_robot_behaviors/motions`. The
camera-driven snapshot sequence is implemented by the interaction manager and
does not generate a YAML file. It moves the UR5e TCP only; this version does
not command a gripper.

## 1. Install and build

Install the Gemini2 first if necessary: [Gemini2 installation](Files/Gemini2_installation.md).

YOLO Pose requires Ultralytics:

```bash
python3 -m pip install --user ultralytics
cd ~/UR5e_social_robotics
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install --packages-select \
  ur5e_interfaces ur5e_motion_server social_robot_perception \
  social_robot_hri social_robot_behaviors
source install/setup.bash
```

The first execution downloads `yolo11n-pose.pt` if it is not already present.

## 2. Configure and calibrate the camera frame

The wrist is measured in the camera optical frame, but the UR5e pose controller
receives poses in the `table` frame. `table` is the same frame used by the
existing UR5e controller to relate its `base_link` to the table.

Edit `src/social_robot_perception/config/pose_3d_params.yaml`:

```yaml
camera_table_tf_node:
  ros__parameters:
    enabled: true
    parent_frame: table
    child_frame: camera_color_optical_frame
    translation_m: [camera_x_m, camera_y_m, camera_z_m]
    rpy_rad: [camera_roll_rad, camera_pitch_rad, camera_yaw_rad]
```

`translation_m` and `rpy_rad` describe the pose of the camera frame expressed
in `table`: the TF relation is `table -> camera_color_optical_frame`. Measure
these six values in metres and radians. The YAML defaults are deliberately
disabled and must not be used for a robot motion.

The `child_frame` and `pose_3d_node.camera_frame` values must match the frame
printed by the camera:

```bash
ros2 topic echo /camera/color/camera_info --once
```

The `camera_table_tf_node` started by the handshake launch publishes this
static transform automatically when `enabled: true`.

After changing the YAML, rebuild and source the workspace so the launch uses
the calibrated configuration:

```bash
cd ~/UR5e_social_robotics
colcon build --symlink-install --packages-select social_robot_perception
source install/setup.bash
```

## 3. Run the demonstration

Open separate terminals and source the workspace in each one:

```bash
source /opt/ros/humble/setup.bash
source ~/UR5e_social_robotics/install/setup.bash
```

Terminal 1 — start the Gemini2:

```bash
ros2 launch orbbec_camera gemini2.launch.py \
  color_width:=640 color_height:=480 color_fps:=15 \
  depth_width:=640 depth_height:=400 depth_fps:=15 \
  depth_registration:=true enable_point_cloud:=false enable_ir:=false
```

Verify the actual camera interfaces before proceeding:

```bash
ros2 topic hz /camera/color/image_raw
ros2 topic hz /camera/depth/image_raw
ros2 topic echo /camera/color/camera_info --once
```

Terminal 2 — start a fake UR5e:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 \
  use_fake_hardware:=true launch_rviz:=false
```

Terminal 3 — start MoveIt:

```bash
ros2 launch ur_moveit_config ur_moveit.launch.py \
  ur_type:=ur5e launch_rviz:=true
```

Terminal 4 — start the pose service:

```bash
ros2 run ur5e_motion_server ur5e_pose_server
```

Terminal 5 — start snapshot perception, gesture interpretation and interaction
management in planning-only mode:

```bash
ros2 launch social_robot_behaviors dynamic_handshake.launch.py execute:=false
```

Terminal 6 — first verify the camera-frame wrist pose:

```bash
ros2 topic echo /wrist_pose
```

The message header must use the configured camera optical frame and its position
must change plausibly in metres as the hand moves. Then verify the calibrated
TF chain:

```bash
ros2 run tf2_ros tf2_echo table camera_color_optical_frame
```

In another terminal, check the detected intent and captured table-frame
snapshot:

```bash
ros2 topic echo /social_intent
ros2 topic echo /handshake_target
```

When the person offers a hand, `/handshake_target` must be reported in the
`table` frame. With `execute:=false`, inspect the requested approach and
contact positions in the `interaction_manager_node` log and confirm them in
MoveIt before allowing any real motion.

## 4. Person action

1. Stand in front of the table, facing the robot and visible to the camera.
2. Keep the right shoulder, elbow, and wrist visible.
3. Extend the right arm naturally towards the robot as if offering a handshake.
4. Hold the pose briefly without speaking.
5. Wait until `/social_intent` prints `handshake_offer`.
6. Confirm that exactly one `/handshake_target` is captured for the gesture.
7. Move away before repeating the gesture.

The thresholds and selected hand can be changed in
`social_robot_hri/config/gesture_interpreter_params.yaml`.

## 5. Real-robot execution

First verify all target coordinates with `execute:=false`. Check the camera
calibration, tool, payload, speed and workspace with the instructor. Replace
the fake driver with the real driver:

```bash
ros2 launch ur_robot_driver ur_control.launch.py \
  ur_type:=ur5e robot_ip:=192.168.0.20 launch_rviz:=false
```

Start the External Control program on the UR5e teach pendant. Only after the
snapshot target and planned sequence are correct, enable the TCP-only
interaction:

```bash
ros2 launch social_robot_behaviors dynamic_handshake.launch.py execute:=true
```

The initial workspace and speed parameters are configured in
`social_robot_behaviors/config/interaction_manager_params.yaml`.

## Current scope and next step

This implementation has one person, one selected wrist and one captured target
per offer. It does not control a gripper, detect physical contact or track a
moving wrist. A later iteration can add filtered wrist tracking after the
static snapshot workflow is calibrated and understood.
