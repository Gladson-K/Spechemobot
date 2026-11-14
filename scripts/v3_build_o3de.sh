#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
O3DE_VERSION="${O3DE_VERSION:-26.05}"
O3DE_HOME="${O3DE_HOME:-/opt/O3DE/${O3DE_VERSION}}"
PROJECT="${ROOT}/sim/o3de/SpechemobotO3DE"
BUILD="${O3DE_BUILD_DIR:-${PROJECT}/build/linux}"

export O3DE_HOME

command -v cmake >/dev/null || { echo "cmake is required"; exit 2; }
command -v ninja >/dev/null || { echo "ninja is required"; exit 2; }

"${ROOT}/scripts/v3_bootstrap_o3de.sh"

cmake_args=(
  -S "${PROJECT}"
  -B "${BUILD}"
  -G "Ninja Multi-Config"
  -DCMAKE_BUILD_TYPE=profile
  -DLY_PROJECTS="${PROJECT}"
)

if [[ -d "${O3DE_HOME}/3rdParty" ]]; then
  cmake_args+=("-DLY_3RDPARTY_PATH=${O3DE_HOME}/3rdParty")
fi

cmake "${cmake_args[@]}"
cmake --build "${BUILD}" --config profile \
  --target SpechemobotO3DE.GameLauncher \
  -j "${BUILD_JOBS:-$(nproc)}"

echo "GameLauncher: ${BUILD}/bin/profile/SpechemobotO3DE.GameLauncher"
