ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop

ARG ROS_DISTRO
ARG USER_UID=1000
ARG USER_GID=1000
ARG TARGETARCH=amd64
ARG ORT_VERSION=1.20.1
ARG O3DE_VERSION=26.05
ARG O3DE_DEB_URL=https://o3debinaries.org/main/Latest/Linux/o3de_2605_0.deb

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV O3DE_HOME=/opt/O3DE/${O3DE_VERSION}
ENV O3DE_EXTRAS_HOME=/opt/o3de-extras
ENV ONNXRUNTIME_ROOT=/opt/onnxruntime
ENV LD_LIBRARY_PATH=/opt/onnxruntime/lib:${LD_LIBRARY_PATH}
ENV GZ_SIM_RESOURCE_PATH=/workspace/Spechemobot/sim/gazebo/models:/workspace/Spechemobot/sim/gazebo/worlds

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake ninja-build git git-lfs curl wget vim less pkg-config ccache \
    python3-colcon-common-extensions python3-rosdep python3-vcstool \
    python3-argcomplete python3-pip python3-venv ruby-full ruby-dev bundler \
    ros-${ROS_DISTRO}-navigation2 ros-${ROS_DISTRO}-nav2-bringup \
    ros-${ROS_DISTRO}-slam-toolbox ros-${ROS_DISTRO}-moveit \
    ros-${ROS_DISTRO}-ros2-control ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-joint-state-publisher ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-xacro ros-${ROS_DISTRO}-tf2-tools ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-rclcpp ros-${ROS_DISTRO}-rclpy \
    ros-${ROS_DISTRO}-sensor-msgs ros-${ROS_DISTRO}-std-msgs \
    ros-${ROS_DISTRO}-geometry-msgs ros-${ROS_DISTRO}-nav-msgs \
    ros-${ROS_DISTRO}-vision-msgs ros-${ROS_DISTRO}-diagnostic-msgs \
    ros-${ROS_DISTRO}-image-transport ros-${ROS_DISTRO}-cv-bridge \
    ros-${ROS_DISTRO}-camera-info-manager ros-${ROS_DISTRO}-rosbag2 \
    ros-${ROS_DISTRO}-rmw-cyclonedds-cpp ros-${ROS_DISTRO}-rmw-fastrtps-cpp \
    libopencv-dev python3-opencv python3-numpy ruby-full \
    libglu1-mesa libglu1-mesa-dev libfontconfig1 libfontconfig1-dev \
    libxcb-randr0 libxcb-randr0-dev libxcb-xinerama0 libxcb-xinerama0-dev \
    libxcb-xinput0 libxcb-xinput-dev libxcb-xfixes0 libxcb-xfixes0-dev \
    libxcb-xkb1 libxcb-xkb-dev libxcb-image0 libxcb-image0-dev \
    libxcb-keysyms1 libxcb-keysyms1-dev libxcb-icccm4 libxcb-render-util0 \
    libxkbcommon0 libxkbcommon-dev libxkbcommon-x11-0 libxkbcommon-x11-dev \
    libcurl4-openssl-dev libpcre2-16-0 zlib1g-dev mesa-common-dev libssl-dev \
    libunwind8 libunwind-dev libzstd-dev xxd \
    libgl1-mesa-dri mesa-vulkan-drivers vulkan-tools \
    libx11-6 libxext6 libxrender1 libxtst6 libxi6 \
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

# Install the O3DE Debian package. The package is the single installation path
# for both Ubuntu 24.04 and 26.04 images; no O3DE source build is performed.
RUN --mount=type=cache,target=/var/cache/o3de,sharing=locked \
    set -eux; \
    deb=/var/cache/o3de/o3de_2605_0.deb; \
    if ! dpkg-deb --info "${deb}" >/dev/null 2>&1; then \
      curl -fL -C - --retry 20 --retry-delay 5 --retry-all-errors \
        -o "${deb}" "${O3DE_DEB_URL}"; \
    fi; \
    if ! dpkg-deb --info "${deb}" >/dev/null 2>&1; then \
      rm -f "${deb}"; \
      curl -fL --retry 20 --retry-delay 5 --retry-all-errors \
        -o "${deb}" "${O3DE_DEB_URL}"; \
    fi; \
    (apt-get install -y "${deb}" || \
      (dpkg -i "${deb}" || true; \
       apt-get update; \
       apt-get -f install -y; \
       dpkg -i "${deb}")); \
    test -d "${O3DE_HOME}" || \
      (echo "O3DE installation directory ${O3DE_HOME} is missing" && exit 1)

RUN "${O3DE_HOME}/python/get_python.sh" && \
    "${O3DE_HOME}/scripts/o3de.sh" register --this-engine

RUN "${O3DE_HOME}/scripts/o3de.sh" register --repo-uri https://canonical.o3de.org && \
    "${O3DE_HOME}/scripts/o3de.sh" download --gem-name LevelGeoreferencing==1.0.0 && \
    "${O3DE_HOME}/scripts/o3de.sh" download --gem-name ROS2==4.2.0 && \
    "${O3DE_HOME}/scripts/o3de.sh" download --gem-name ROS2Controllers==1.1.0 && \
    "${O3DE_HOME}/scripts/o3de.sh" download --gem-name ROS2Sensors==1.0.1

# O3DE Extras carries the robotics templates and the split sensor/controller gems.
RUN git clone --depth 1 https://github.com/o3de/o3de-extras.git "${O3DE_EXTRAS_HOME}" && \
    git -C "${O3DE_EXTRAS_HOME}" lfs install --local && \
    git -C "${O3DE_EXTRAS_HOME}" lfs pull && \
    "${O3DE_HOME}/scripts/o3de.sh" register --all-gems-path "${O3DE_EXTRAS_HOME}/Gems/" && \
    "${O3DE_HOME}/scripts/o3de.sh" register --all-templates-path "${O3DE_EXTRAS_HOME}/Templates/"

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
