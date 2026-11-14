#!/usr/bin/env bash
set -euo pipefail

export ROS_DISTRO="${ROS_DISTRO:-jazzy}"
export O3DE_HOME="${O3DE_HOME:-/opt/O3DE/26.05}"
export O3DE_EXTRAS_HOME="${O3DE_EXTRAS_HOME:-/opt/o3de-extras}"

if [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

if [[ -f /workspace/Spechemobot/ros2_ws/install/setup.bash ]]; then
  # shellcheck disable=SC1091
  source /workspace/Spechemobot/ros2_ws/install/setup.bash
fi

export PATH="${O3DE_HOME}/scripts:${PATH}"
exec "$@"
