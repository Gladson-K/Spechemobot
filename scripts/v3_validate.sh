#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose v2 is required: docker compose version"
  exit 2
fi

echo "== Source syntax =="
python3 - <<'PY'
import pathlib
import sys

failed = False
for path in sorted(pathlib.Path("ros2_ws/src").rglob("*.py")):
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as error:
        failed = True
        print(f"{path}:{error.lineno}: {error.msg}", file=sys.stderr)
if failed:
    sys.exit(1)
print("Python syntax: OK")
PY

python3 - <<'PY'
import pathlib
import sys
import xml.etree.ElementTree as ET

failed = False
patterns = ("*.xml", "*.sdf", "*.urdf", "*.xacro", "*.world")
for pattern in patterns:
    for path in sorted(pathlib.Path(".").rglob(pattern)):
        if any(part in {".git", "build", "install", "log"} for part in path.parts):
            continue
        try:
            ET.parse(path)
        except ET.ParseError as error:
            failed = True
            print(f"{path}: {error}", file=sys.stderr)
if failed:
    sys.exit(1)
print("XML/SDF/URDF: OK")
PY

python3 - <<'PY'
import json
import pathlib
import sys

failed = False
for path in sorted(pathlib.Path(".").rglob("*.json")):
    if any(part in {".git", "build", "install", "log"} for part in path.parts):
        continue
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        failed = True
        print(f"{path}: {error}", file=sys.stderr)
if failed:
    sys.exit(1)
print("JSON: OK")
PY

python3 - <<'PY'
import pathlib
import sys

try:
    import yaml
except ImportError:
    print("YAML: skipped (PyYAML not installed)")
    sys.exit(0)

failed = False
for pattern in ("*.yaml", "*.yml"):
    for path in sorted(pathlib.Path(".").rglob(pattern)):
        if any(part in {".git", "build", "install", "log"} for part in path.parts):
            continue
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            failed = True
            print(f"{path}: {error}", file=sys.stderr)
if failed:
    sys.exit(1)
print("YAML: OK")
PY

for file in scripts/*.sh deployment/docker-v3/*/entrypoint.sh; do
  [[ -f "$file" ]] || continue
  bash -n "$file"
done
echo "Shell syntax: OK"

if command -v ruby >/dev/null 2>&1; then
  while IFS= read -r file; do
    ruby -c "$file" >/dev/null
  done < <(find orchestration/ruby -type f \( -name '*.rb' -o -path '*/bin/*' \) | sort)
  ruby orchestration/ruby/test/ros2_cli_test.rb
  ruby orchestration/ruby/test/orchestrator_test.rb
  echo "Ruby: OK"
else
  echo "Ruby: skipped (ruby not installed)"
fi

echo "== Compose configuration =="
if [[ ! -f deployment/docker-v3/.env ]]; then
  echo "warning: deployment/docker-v3/.env is missing; using defaults from compose"
fi
"${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile all config -q
echo "Compose config: OK"

if [[ "${VALIDATE_DOCKER_BUILD:-0}" == "1" ]]; then
  echo "== Image build (gazebo-jazzy) =="
  "${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile gazebo-jazzy build gazebo-jazzy
fi

running="$("${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile all ps --services --filter status=running 2>/dev/null || true)"

if grep -qx 'gazebo-jazzy' <<<"$running"; then
  echo "== Gazebo Jazzy runtime =="
  "${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile all exec -T gazebo-jazzy bash -lc '
    source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
    command -v ros2
    command -v colcon
    command -v gz
    ros2 pkg prefix ros_gz_bridge
    if [[ -f /workspace/Spechemobot/ros2_ws/install/setup.bash ]]; then
      source /workspace/Spechemobot/ros2_ws/install/setup.bash
      ros2 pkg executables spechemobot_process
      ros2 launch spechemobot_bringup sim.launch.py --show-args >/dev/null
    else
      echo "ros2_ws/install not found; build with colcon first"
    fi
  '
else
  echo "Gazebo Jazzy runtime: skipped (service not running)"
fi

if grep -qx 'o3de-jazzy' <<<"$running"; then
  echo "== O3DE Jazzy runtime =="
  "${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile all exec -T o3de-jazzy bash -lc '
    test -x /opt/O3DE/26.05/scripts/o3de.sh
    /opt/O3DE/26.05/scripts/o3de.sh --help >/dev/null
    test -f /workspace/Spechemobot/sim/o3de/SpechemobotO3DE/project.json
  '
else
  echo "O3DE Jazzy runtime: skipped (service not running)"
fi

if [[ "${VALIDATE_COLCON_BUILD:-0}" == "1" || "${VALIDATE_COLCON_TEST:-0}" == "1" ]]; then
  echo "== ROS 2 workspace build and tests =="
  "${COMPOSE[@]}" -f deployment/docker-v3/docker-compose.yaml --profile dev run --rm --no-deps ros2-dev-jazzy bash -lc '
    set -e
    source /opt/ros/${ROS_DISTRO:-jazzy}/setup.bash
    cd /workspace/Spechemobot/ros2_ws
    export MAKEFLAGS=-j2
    colcon build --symlink-install --parallel-workers 2 --event-handlers console_direct+
    if [[ "'"${VALIDATE_COLCON_TEST:-0}"'" == "1" ]]; then
      source install/setup.bash
      colcon test --parallel-workers 2 --event-handlers console_direct+
      colcon test-result --verbose
    fi
  '
fi

echo "Validation completed."
