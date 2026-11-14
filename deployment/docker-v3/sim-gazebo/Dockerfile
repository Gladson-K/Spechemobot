ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop

ARG ROS_DISTRO
ARG USER_UID=1000
ARG USER_GID=1000
ARG TARGETARCH=amd64
ARG ORT_VERSION=1.20.1

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ONNXRUNTIME_ROOT=/opt/onnxruntime
ENV LD_LIBRARY_PATH=/opt/onnxruntime/lib:${LD_LIBRARY_PATH}
ENV GZ_SIM_RESOURCE_PATH=/workspace/Spechemobot/sim/gazebo/models:/workspace/Spechemobot/sim/gazebo/worlds

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git curl wget vim less pkg-config ccache \
    python3-colcon-common-extensions python3-rosdep python3-vcstool \
    python3-argcomplete python3-pip python3-venv ruby-full ruby-dev bundler \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-navigation2 ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-slam-toolbox ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-ros2-control ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-gz-ros2-control ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-robot-state-publisher ros-${ROS_DISTRO}-xacro \
    ros-${ROS_DISTRO}-tf2-tools ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-rclcpp ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-demo-nodes-cpp ros-${ROS_DISTRO}-demo-nodes-py \
    ros-${ROS_DISTRO}-sensor-msgs ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-geometry-msgs ros-${ROS_DISTRO}-nav-msgs \
    ros-${ROS_DISTRO}-vision-msgs ros-${ROS_DISTRO}-diagnostic-msgs \
    ros-${ROS_DISTRO}-image-transport ros-${ROS_DISTRO}-image-transport-plugins \
    ros-${ROS_DISTRO}-cv-bridge ros-${ROS_DISTRO}-camera-info-manager \
    ros-${ROS_DISTRO}-rosbag2 ros-${ROS_DISTRO}-rosbag2-storage-mcap \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp ros-${ROS_DISTRO}-rmw-fastrtps-cpp \
    libopencv-dev python3-opencv python3-numpy \
    v4l-utils libusb-1.0-0-dev libgpiod-dev \
    libgl1-mesa-dri mesa-vulkan-drivers vulkan-tools libglu1-mesa \
    libx11-6 libxext6 libxrender1 libxtst6 libxi6 \
    libxcb-randr0 libxcb-xinerama0 libxcb-xinput0 libxcb-xfixes0 \
    libxcb-xkb1 libxcb-image0 libxcb-keysyms1 libxkbcommon-x11-0 \
    xvfb xauth iproute2 iputils-ping netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir --break-system-packages \
      onnx onnxruntime || \
    echo "warning: Python ONNX packages unavailable; C++ ONNX Runtime remains available"

RUN case "${TARGETARCH}" in \
      amd64) ORT_ARCH=x64 ;; \
      arm64) ORT_ARCH=aarch64 ;; \
      *) echo "unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/microsoft/onnxruntime/releases/download/v${ORT_VERSION}/onnxruntime-linux-${ORT_ARCH}-${ORT_VERSION}.tgz" \
      -o /tmp/onnxruntime.tgz && \
    tar -xzf /tmp/onnxruntime.tgz -C /opt && \
    ln -s "/opt/onnxruntime-linux-${ORT_ARCH}-${ORT_VERSION}" /opt/onnxruntime && \
    rm /tmp/onnxruntime.tgz

RUN set -eux; \
    if ! getent group "${USER_GID}" >/dev/null; then groupadd -g "${USER_GID}" dev; fi; \
    if ! getent passwd "${USER_UID}" >/dev/null; then useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash dev; fi; \
    user_name="$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
    install -d -m 0755 -o "${USER_UID}" -g "${USER_GID}" /home/dev; \
    if getent group video >/dev/null; then usermod -aG video "${user_name}" || true; fi; \
    if getent group render >/dev/null; then usermod -aG render "${user_name}" || true; fi; \
    echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/dev/.bashrc; \
    chown -R "${USER_UID}:${USER_GID}" /home/dev

ENV HOME=/home/dev

COPY --chmod=755 entrypoint.sh /usr/local/bin/spechemobot-entrypoint

USER ${USER_UID}:${USER_GID}
WORKDIR /workspace/Spechemobot
ENTRYPOINT ["/usr/local/bin/spechemobot-entrypoint"]
CMD ["bash"]
