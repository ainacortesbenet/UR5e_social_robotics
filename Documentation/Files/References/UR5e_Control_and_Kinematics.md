# UR5e control and kinematics

These optional examples exercise the ROS 2 movement utilities directly. Use the
[fake-hardware setup](../../4a_ROS2_Session.md#3-simulation-with-fake-hardware)
to start the UR driver. For the MoveIt examples, also start MoveIt 2 and RViz.

## Joint targets

The single-target launch takes six joint angles in degrees and a time in seconds.
Run this in a separate terminal with the workspace sourced.

```bash
ros2 launch ur5e_kinematics_control ur5e_joint_target.launch.py \
  target_deg:="[-90.0, -90.0, -90.0, -180.0, -90.0, 90.0]" time_sec:=5.0 \
  controller_topic:=/joint_trajectory_controller/joint_trajectory
```

For multiple targets, the trajectory YAML uses cumulative times from the start
of the trajectory. For example, times of 2 and 5 seconds place the second point
3 seconds after the first.

```bash
ros2 launch ur5e_kinematics_control ur5e_joint_targets.launch.py \
  trajectory_file:=trajectory_handshake.yaml
```

Use the controller topic for the driver you launched. With fake hardware, check
that `/joint_trajectory_controller/joint_trajectory` is active.

## Forward kinematics with MoveIt 2

Forward kinematics computes the end-effector pose from six joint angles.
MoveIt's `move_group` provides `/compute_fk`. Set `execute:=false` to inspect
the result.

```bash
ros2 launch ur5e_robot_controller ur5e_fkine.launch.py \
  joints:="[0.0, -90.0, 90.0, -90.0, -90.0, 0.0]" execute:=false
```

## Inverse kinematics with MoveIt 2

Inverse kinematics uses `/compute_ik` to find a joint solution for a target
pose. The pose example uses millimetres and degrees. Start with the current
joint state as the IK seed. If necessary, set `seed_from_joint_states:=false`
and supply six `seed_joints` angles in degrees to select a different
configuration.

```bash
ros2 launch ur5e_robot_controller ur5e_pose.launch.py \
  target_xyz:="[-100.0, -300.0, 300.0]" \
  target_rpy:="[90.0, 0.0, 0.0]" seed_from_joint_states:=true
```

The classroom sequences express RoboDK targets in the `table` frame. The
pose tools transform them into the MoveIt planning frame, `base_link`, using
TF. In the classroom transform, `table` is rotated 180° around the vertical
axis relative to `base_link`. For the social motion YAML and its normal
execution path, see [Session 2](../../4a_ROS2_Session.md#define-your-social-movement).
