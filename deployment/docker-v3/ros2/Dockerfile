ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop

ARG ROS_DISTRO
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git curl wget vim less \
    python3-colcon-common-extensions python3-rosdep python3-vcstool \
    python3-argcomplete python3-pip pkg-config ccache ruby-full ruby-dev bundler \
    ros-${ROS_DISTRO}-demo-nodes-cpp ros-${ROS_DISTRO}-demo-nodes-py \
    ros-${ROS_DISTRO}-rclcpp ros-${ROS_DISTRO}-sensor-msgs \
    ros-${ROS_DISTRO}-std-msgs ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-image-transport ros-${ROS_DISTRO}-image-tools \
    ros-${ROS_DISTRO}-vision-msgs ros-${ROS_DISTRO}-rosbag2 \
    libopencv-dev v4l-utils libusb-1.0-0-dev libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    if ! getent group "${USER_GID}" >/dev/null; then groupadd -g "${USER_GID}" dev; fi; \
    if ! getent passwd "${USER_UID}" >/dev/null; then useradd -m -u "${USER_UID}" -g "${USER_GID}" -s /bin/bash dev; fi; \
    user_name="$(getent passwd "${USER_UID}" | cut -d: -f1)"; \
    install -d -m 0755 -o "${USER_UID}" -g "${USER_GID}" /home/dev; \
    if getent group video >/dev/null; then usermod -aG video "${user_name}" || true; fi; \
    echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/dev/.bashrc; \
    chown -R "${USER_UID}:${USER_GID}" /home/dev

ENV HOME=/home/dev

USER ${USER_UID}:${USER_GID}
WORKDIR /workspace/Spechemobot
CMD ["bash"]
