#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${SPECHEMOBOT_TARGET_ROOT:-}" ]]; then
  ROOT="$(cd "$SPECHEMOBOT_TARGET_ROOT" && pwd)"
elif git -C "$PACKAGE_ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$PACKAGE_ROOT" rev-parse --show-toplevel)"
else
  echo "Run this from inside an existing Spechemobot Git checkout, or set:"
  echo "  SPECHEMOBOT_TARGET_ROOT=/absolute/path/to/Spechemobot"
  exit 2
fi

if [[ "$PACKAGE_ROOT" == "$ROOT" ]]; then
  echo "Already running inside the repository root: $ROOT"
  exit 0
fi

[[ -f "$PACKAGE_ROOT/.gitmodules" ]] || { echo "Package .gitmodules not found"; exit 2; }

mkdir -p "$ROOT/third_party" \
         "$ROOT/deployment/docker-v3" \
         "$ROOT/scripts" "$ROOT/docs" \
         "$ROOT/ros2_ws/src" "$ROOT/sim/gazebo" "$ROOT/sim/o3de" \
         "$ROOT/orchestration" "$ROOT/datasets" "$ROOT/models"

cp "$PACKAGE_ROOT/.gitmodules" "$ROOT/.gitmodules"
cp "$PACKAGE_ROOT/.gitignore" "$ROOT/.gitignore"
cp "$PACKAGE_ROOT/README_V3.md" "$ROOT/README_V3.md"

for dir in deployment docs scripts ros2_ws sim orchestration datasets models; do
  if [[ -d "$PACKAGE_ROOT/$dir" ]]; then
    cp -a "$PACKAGE_ROOT/$dir/." "$ROOT/$dir/"
  fi
done

chmod +x "$ROOT"/scripts/v3_*.sh
chmod +x "$ROOT"/orchestration/ruby/bin/* 2>/dev/null || true

echo "V3 overlay installed into: $ROOT"
echo "Next: cd '$ROOT' && bash scripts/v3_init_submodules.sh"
