FROM osrf/ros:humble-desktop-full

SHELL ["/bin/bash", "-c"]

# Avoid transient APT download failures
RUN echo 'Acquire::Retries "6";' > /etc/apt/apt.conf.d/80-retries

# Fix expired ROS 2 GPG key (avoid GPG errors in apt)
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros2-latest-archive-keyring.gpg

# ============================================================================
# Base system tools + X11/OpenGL support
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    x11-apps \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglu1-mesa \
    mesa-utils \
    libqt5x11extras5 \
    libxkbcommon-x11-0 \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxtst6 \
    build-essential \
    cmake \
    pkg-config \
    python3-colcon-common-extensions \
    python3-dev \
    python3-pip \
    python3-rosdep \
    python3-venv \
    portaudio19-dev \
    espeak-ng \
    unzip \
    git \
    wget \
    gpg \
    apt-transport-https \
    iputils-ping \
    usbutils \
    v4l-utils \
    libssl-dev \
    libusb-1.0-0-dev \
    libudev-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# General ROS 2 extra tools
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-rviz2 \
    ros-humble-joint-state-publisher \
    ros-humble-joint-state-publisher-gui \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-teleop-twist-keyboard \
    ros-humble-rosbridge-server \
    ros-humble-tf-transformations \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Gazebo Classic + Nav2 + Cartographer
# NOTE: libgazebo-dev removed unless you really need to compile Gazebo plugins
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    gazebo \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-gazebo-plugins \
    ros-humble-gazebo-ros2-control \
    ros-humble-nav2-bringup \
    ros-humble-nav2-simple-commander \
    ros-humble-cartographer-ros \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# MoveIt 2 + Universal Robots + ros2_control
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-moveit \
    ros-humble-moveit-visual-tools \
    ros-humble-moveit-servo \
    ros-humble-ur-description \
    ros-humble-ur-moveit-config \
    ros-humble-ur-robot-driver \
    ros-humble-ros2-control \
    ros-humble-ros2-controllers \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# rosdep init (safe if already initialized)
# ============================================================================
RUN rosdep init || true && rosdep update

# ============================================================================
# Add Microsoft GPG key and VS Code APT repository (no Snap)
# ============================================================================
RUN set -eux; \
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg; \
    install -D -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/microsoft.gpg; \
    rm -f microsoft.gpg; \
    printf "Types: deb\nURIs: https://packages.microsoft.com/repos/code\nSuites: stable\nComponents: main\nArchitectures: amd64\nSigned-By: /usr/share/keyrings/microsoft.gpg\n" \
      > /etc/apt/sources.list.d/vscode.sources; \
    apt-get update; \
    apt-get install -y --no-install-recommends code; \
    rm -rf /var/lib/apt/lists/*

# ============================================================================
# Orbbec Gemini 2 camera support (ROS 2 Humble binary driver)
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-orbbec-camera \
    ros-humble-orbbec-description \
    ros-humble-image-transport \
    ros-humble-image-transport-plugins \
    ros-humble-compressed-image-transport \
    ros-humble-camera-info-manager \
    ros-humble-image-publisher \
    ros-humble-diagnostic-updater \
    ros-humble-diagnostic-msgs \
    ros-humble-statistics-msgs \
    ros-humble-xacro \
    ros-humble-backward-ros \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Intel RealSense ROS 2 wrapper (binary)
# Keep this separate from librealsense compilation for easier debugging
# ============================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-humble-realsense2-camera \
    ros-humble-realsense2-description \
    ros-humble-image-transport \
    ros-humble-camera-info-manager \
    ros-humble-diagnostic-updater \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# Build librealsense from source with RSUSB backend
# This is the part that helps when the RealSense camera is not detected well
# inside Docker through the standard backend.
# ============================================================================
RUN mkdir -p /opt/realsense-src && \
    cd /opt/realsense-src && \
    git clone --depth 1 https://github.com/IntelRealSense/librealsense.git && \
    cd librealsense && \
    mkdir build && cd build && \
    cmake .. \
      -DCMAKE_BUILD_TYPE=Release \
      -DFORCE_RSUSB_BACKEND=ON \
      -DBUILD_EXAMPLES=false && \
    make -j"$(nproc)" && \
    make install && \
    ldconfig && \
    cd / && rm -rf /opt/realsense-src
    
# ============================================================================
# Default ROS 2 environment in bashrc
# ============================================================================
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc

CMD ["bash"]
