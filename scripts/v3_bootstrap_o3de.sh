#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
O3DE_VERSION="${O3DE_VERSION:-26.05}"
O3DE_HOME="${O3DE_HOME:-/opt/O3DE/${O3DE_VERSION}}"
O3DE_EXTRAS_HOME="${O3DE_EXTRAS_HOME:-/opt/o3de-extras}"
O3DE="${O3DE_HOME}/scripts/o3de.sh"
PROJECT="${ROOT}/sim/o3de/SpechemobotO3DE"

if [[ ! -x "${O3DE}" ]]; then
  echo "O3DE CLI not found: ${O3DE}"
  echo "Install the O3DE .deb image first, or set O3DE_HOME to the SDK root."
  exit 2
fi

if [[ ! -f "${PROJECT}/project.json" ]]; then
  echo "O3DE project manifest not found: ${PROJECT}/project.json"
  exit 2
fi

"${O3DE}" register --this-engine

if [[ -d "${O3DE_EXTRAS_HOME}/Gems" ]]; then
  "${O3DE}" register --all-gems-path "${O3DE_EXTRAS_HOME}/Gems" || true
fi

if [[ -d "${O3DE_EXTRAS_HOME}/Templates" ]]; then
  "${O3DE}" register --all-templates-path "${O3DE_EXTRAS_HOME}/Templates" || true
fi

"${O3DE}" register -p "${PROJECT}"

if ! "${O3DE}" edit-project-properties -pp "${PROJECT}" --user -ep "${O3DE_HOME}"; then
  echo "warning: could not write ${PROJECT}/user/project.json; O3DE_HOME is still used by CMake"
fi

echo "O3DE engine registered: ${O3DE_HOME}"
echo "O3DE project registered: ${PROJECT}"
