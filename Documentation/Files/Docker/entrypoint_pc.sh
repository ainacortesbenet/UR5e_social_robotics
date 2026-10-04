#!/bin/bash
set -e

# Source ROS 2 Humble
source /opt/ros/humble/setup.bash

# Source project setup only if it has been built
if [ -f /root/UR5e_social_robotics/install/setup.bash ]; then
  source /root/UR5e_social_robotics/install/setup.bash
else
  echo "[entrypoint] Workspace not built yet; skipping /root/UR5e_social_robotics/install/setup.bash"
fi

# Activate the Humble Python environment when it has already been created in
# the bind-mounted repository.
if [ -f /root/UR5e_social_robotics/.venv-humble/bin/activate ]; then
  source /root/UR5e_social_robotics/.venv-humble/bin/activate
fi

# DDS / ROS 2 networking (clear & explicit)
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Teaching banner
echo "=============================================="
echo " ROS 2 Humble - Docker PC"
echo "----------------------------------------------"
echo " ROS_DOMAIN_ID                  = $ROS_DOMAIN_ID"
echo " ROS_AUTOMATIC_DISCOVERY_RANGE  = $ROS_AUTOMATIC_DISCOVERY_RANGE"
echo " ROS_STATIC_PEERS               = $ROS_STATIC_PEERS"
echo " CYCLONEDDS_URI                 = $CYCLONEDDS_URI"
echo "=============================================="

cd /root/UR5e_social_robotics

exec "$@"
