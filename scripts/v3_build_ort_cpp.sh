#!/usr/bin/env bash
# Optional source build of ONNX Runtime C/C++ shared library.
# The Docker images install a pinned prebuilt runtime by default; use this only
# when a custom provider or the exact upstream source is required.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ORT="$ROOT/third_party/onnxruntime"
BUILD="$ROOT/build/onnxruntime"

if [[ ! -f "$ORT/CMakeLists.txt" ]]; then
  echo "ONNX Runtime submodule not found. Run scripts/v3_init_submodules.sh first."
  exit 2
fi

mkdir -p "$BUILD"
cd "$ORT"
./build.sh --config Release --build_shared_lib --parallel "${BUILD_JOBS:-$(nproc)}" \
  --cmake_extra_defines CMAKE_INSTALL_PREFIX="$BUILD/install"

echo "Build finished. Inspect $ORT/build/Linux/Release and install artifacts under $BUILD/install."
