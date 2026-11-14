#!/usr/bin/env bash
set -euo pipefail

export ROS_DISTRO="${ROS_DISTRO:-jazzy}"

if [[ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]]; then
  # shellcheck disable=SC1090
  source "/opt/ros/${ROS_DISTRO}/setup.bash"
fi

if [[ -f /workspace/Spechemobot/ros2_ws/install/setup.bash ]]; then
  # shellcheck disable=SC1091
  source /workspace/Spechemobot/ros2_ws/install/setup.bash
fi

exec "$@"
