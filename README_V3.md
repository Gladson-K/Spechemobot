# Spechemobot V3

Reproducible ROS 2 and simulation environments for chemical-process robotics. V3 covers two Ubuntu/ROS 2 pairs and two simulators:

| Ubuntu | ROS 2 | Gazebo | O3DE |
| --- | --- | --- | --- |
| 24.04 | Jazzy | Harmonic via `ros-jazzy-ros-gz` | 26.05 from the Debian package |
| 26.04 | Lyrical | Jetty via `ros-lyrical-ros-gz` | 26.05 from the Debian package |

O3DE is installed once from `o3de_2605_0.deb`. There is no Yocto layer, kernel build, or O3DE source build in V3.

## Layout

```text
deployment/docker-v3/     Docker images, compose profiles, GPU/headless overrides
ros2_ws/src/              ROS 2 packages (messages, sim bringup, process, perception, orchestration, datasets, evaluation)
sim/gazebo/               Gazebo worlds and models
sim/o3de/                 O3DE project scaffold and build scripts
orchestration/ruby/       Experimental Ruby supervisor and HTTP API
datasets/                 Recorded and processed datasets
models/                   ONNX models
scripts/                  Bootstrap, validation, and build helpers
docs/                     Acceptance gates and platform notes
```

## Host requirements

- Linux with Docker Engine and Docker Compose v2 (`docker compose version`).
- Git and Git LFS for O3DE assets.
- 16 GB RAM recommended for Gazebo, 32 GB for O3DE and image builds.
- 40 GB free disk minimum; 100 GB recommended for all images and datasets.
- Vulkan-capable GPU for O3DE GUI. Use `O3DE_RHI=null` for headless runs.
- A display for Gazebo and RViz, or use the headless override.

## First start

```bash
cd deployment/docker-v3
cp .env.example .env
$EDITOR .env
docker compose --profile gazebo-jazzy build
docker compose --profile gazebo-jazzy up -d
docker compose exec gazebo-jazzy bash
```

The repository is mounted at `/workspace/Spechemobot`. Build the ROS 2 workspace once inside a container:

```bash
cd /workspace/Spechemobot/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Profiles and services

| Profile | Services | Purpose |
| --- | --- | --- |
| `gazebo-jazzy` | `gazebo-jazzy` | Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic |
| `gazebo-lyrical` | `gazebo-lyrical` | Ubuntu 26.04, ROS 2 Lyrical, Gazebo Jetty |
| `o3de-jazzy` | `o3de-jazzy` | Jazzy with O3DE 26.05 |
| `o3de-lyrical` | `o3de-lyrical` | Lyrical with O3DE 26.05 |
| `runtime` | `runtime-jazzy`, `runtime-lyrical` | ONNX Runtime and OpenCV runtime |
| `dev` | `ros2-dev-jazzy`, `ros2-dev-lyrical` | Minimal ROS 2 development shell |
| `compiler` | `compiler` | LLVM/MLIR compiler image |
| `all` | every service | Build or validate the full matrix |

Run only one simulator per ROS domain unless you intend cross-talk. The compose file assigns separate default domains per service.

## Worlds

| World file | Launch |
| --- | --- |
| `sim/gazebo/worlds/reactor_hall.sdf` | `ros2 launch spechemobot_bringup reactor_hall.launch.py` |
| `sim/gazebo/worlds/furnace_annealing.sdf` | `ros2 launch spechemobot_bringup furnace_annealing.launch.py` |
| `sim/gazebo/worlds/conveyor_sorting.sdf` | `ros2 launch spechemobot_bringup conveyor_sorting.launch.py` |
| `sim/gazebo/worlds/sensor_qualification.sdf` | `ros2 launch spechemobot_bringup sensor_qualification.launch.py` |

Set `SIM_WORLD` to pick the default world for `sim.launch.py`. Add `headless:=true` for CI.

## O3DE

```bash
docker compose --profile o3de-jazzy up -d
docker compose exec o3de-jazzy bash
cd /workspace/Spechemobot
bash scripts/v3_bootstrap_o3de.sh
bash scripts/v3_build_o3de.sh
ros2 launch spechemobot_bringup sim.launch.py sim_backend:=o3de world:=reactor_hall
```

The checked-in O3DE project is a buildable scaffold with an empty `Spechemobot` level. Create the four production levels in the O3DE Editor and keep ROS 2 topic names aligned with `ros2_ws/src/spechemobot_bringup/config/gz_bridge.yaml`. Gazebo SDF is not imported into O3DE.

## ROS 2 interfaces

- `/process/state` (`spechemobot_msgs/msg/ProcessState`)
- `/process/run_batch` (`spechemobot_msgs/action/RunBatch`)
- `/robot/pick_place` (`spechemobot_msgs/action/PickPlace`)
- `/robot/tasks` (`spechemobot_msgs/msg/RobotTask`)
- `/safety/alarm`, `/safety/estop`, `/safety/reset`
- `/containers/C_001/state` through `/containers/C_004/state`
- `/camera/image_raw`, `/thermal_camera`, `/perception/thermal_reading`

Start a batch from the command line:

```bash
ros2 action send_goal /process/run_batch spechemobot_msgs/action/RunBatch \
  "{batch_id: batch-1, target_temperature_c: 450.0, hold_time_s: 8.0, product_id: P-100}" --feedback
```

## Datasets and evaluation

```bash
ros2 launch spechemobot_bringup reactor_hall.launch.py launch_recording:=true session_name:=calibration-01
ros2 run spechemobot_dataset make_manifest --root datasets/raw --output datasets/processed/manifest.json
ros2 launch spechemobot_bringup reactor_hall.launch.py launch_eval:=true eval_duration_s:=120
```

Thermal inference expects `models/spechemobot_thermal.onnx` unless `model_path` is overridden. Without ONNX Runtime or a model, the perception node still publishes thermal statistics from the image.

## Experimental Ruby orchestration

```bash
orchestration/ruby/bin/spechemobot-orchestrator health
orchestration/ruby/bin/spechemobot-orchestrator batch --target 425 --hold 6
orchestration/ruby/bin/spechemobot-orchestrator --http --port 8090
```

The Ruby process shells out to the `ros2` CLI. It is not a safety controller and provides no real-time guarantees.

## Validation and tests

Source, config, Ruby, and Compose validation:

```bash
bash scripts/v3_validate.sh
```

Build and run the ROS 2 unit tests in the dev image:

```bash
VALIDATE_COLCON_TEST=1 bash scripts/v3_validate.sh
```

Or run the same path manually:

```bash
docker compose -f deployment/docker-v3/docker-compose.yaml --profile dev run --rm --no-deps ros2-dev-jazzy bash -lc '
  source /opt/ros/jazzy/setup.bash
  cd /workspace/Spechemobot/ros2_ws
  colcon build --symlink-install
  source install/setup.bash
  colcon test --event-handlers console_cohesion+
  colcon test-result --verbose
'
```

Tests live in each Python package under `test/`. The current suite covers process and safety models, batch orchestration, dataset manifests, runtime evaluation, and launch-file construction.

For the full container build matrix:

```bash
cd deployment/docker-v3
docker compose --profile all build
```

## Troubleshooting

- `docker compose: command not found`: install Docker Compose v2. The legacy `docker-compose` v1 is not supported for this compose file.
- `ros2: command not found`: source `/opt/ros/$ROS_DISTRO/setup.bash` or use a ROS image, not the runtime image.
- Gazebo cannot open a window: export `DISPLAY`, mount `/tmp/.X11-unix`, and allow local X11 clients; use `headless:=true` for CI.
- O3DE fails to find an engine: run `bash scripts/v3_bootstrap_o3de.sh` in the O3DE image and confirm `O3DE_HOME=/opt/O3DE/26.05`.
- O3DE RHI failures: use `O3DE_RHI=vulkan` on a Vulkan host, or `O3DE_RHI=null` headless.
- ROS 2 nodes cannot see each other: all compose services use host networking; keep `ROS_DOMAIN_ID` identical for nodes that must communicate.
- ONNX Runtime missing: verify `/opt/onnxruntime/lib/libonnxruntime.so` and rebuild `spechemobot_perception`.
