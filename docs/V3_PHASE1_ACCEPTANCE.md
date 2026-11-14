# V3 Phase-1 acceptance gates

Run the gates in order. Do not mark a gate complete while any command in it fails.

## Gate 0 - host and Docker

- [ ] `docker version` works without sudo.
- [ ] `docker compose version` reports v2.40 or newer.
- [ ] `docker info` shows the expected storage driver and enough free disk.
- [ ] Git LFS is installed (`git lfs version`).
- [ ] A Vulkan device is available for GUI O3DE, or `O3DE_RHI=null` is accepted for headless.

## Gate 1 - repository and submodules

- [ ] `git submodule update --init --recursive` completes.
- [ ] `git submodule status` shows commit IDs with no leading `-`.
- [ ] `third_party/o3de-extras` assets are present after `git lfs pull`.
- [ ] `scripts/v3_install_overlay.sh` is not required when building from this checkout directly.

## Gate 2 - compose configuration

```bash
cd deployment/docker-v3
cp .env.example .env
docker compose config -q
docker compose --profile all config -q
```

- [ ] Both commands exit 0.
- [ ] `.env` contains host `USER_UID` and `USER_GID`.
- [ ] No Yocto service or profile remains in the rendered configuration.

## Gate 3 - image builds

Build the minimal pair first, then the full matrix:

```bash
docker compose --profile gazebo-jazzy build
docker compose --profile gazebo-lyrical build
docker compose --profile runtime build
docker compose --profile dev build
docker compose --profile compiler build
docker compose --profile o3de-jazzy build
docker compose --profile o3de-lyrical build
```

- [ ] Each image builds without manual package installation.
- [ ] `spechemobot/sim-gazebo:jazzy` contains `gz`, `ros2`, and `colcon`.
- [ ] `spechemobot/sim-o3de:jazzy` contains `/opt/O3DE/26.05/scripts/o3de.sh`.
- [ ] O3DE reports `o3de-sdk` as the registered engine name.
- [ ] `LevelGeoreferencing`, `ROS2`, `ROS2Controllers`, and `ROS2Sensors` are registered.
- [ ] ONNX Runtime shared library exists at `/opt/onnxruntime/lib/libonnxruntime.so`.

## Gate 4 - ROS 2 workspace

```bash
docker compose --profile gazebo-jazzy up -d
docker compose exec gazebo-jazzy bash -lc '
  cd /workspace/Spechemobot/ros2_ws
  rosdep install --from-paths src --ignore-src -r -y
  colcon build --symlink-install --event-handlers console_direct+
  source install/setup.bash
  colcon test --event-handlers console_direct+
  colcon test-result --verbose
  ros2 pkg list | grep spechemobot
'
```

- [ ] `spechemobot_msgs` generates Python and C++ interfaces.
- [ ] `spechemobot_perception` builds with or without ONNX Runtime and reports which path was used.
- [ ] All Python packages install their launch, config, and resource files.
- [ ] `ros2 pkg executables spechemobot_process` lists the four process nodes.
- [ ] Unit tests under each Python package `test/` pass.

## Gate 5 - Gazebo worlds

For each world, launch headless and verify the expected topics:

```bash
ros2 launch spechemobot_bringup reactor_hall.launch.py headless:=true
ros2 launch spechemobot_bringup furnace_annealing.launch.py headless:=true
ros2 launch spechemobot_bringup conveyor_sorting.launch.py headless:=true
ros2 launch spechemobot_bringup sensor_qualification.launch.py headless:=true
```

In a second shell:

```bash
ros2 topic list | grep -E '^/(clock|camera|thermal|scan|points|imu|navsat|magnetometer|air_pressure|altimeter|contact|logical_camera|odom|cmd_vel)'
ros2 topic hz /clock
```

- [ ] The world loads without SDF errors.
- [ ] `/clock` publishes at the expected simulation rate.
- [ ] RGB, depth, RGBD, thermal, segmentation, wide-angle, lidar, IMU, NavSat, magnetometer, air-pressure, altimeter, contact, and logical-camera topics appear.
- [ ] The AMR responds to `/cmd_vel` and publishes `/odom`.
- [ ] No sensor plugin reports a missing system plugin.

## Gate 6 - process, robot, and safety

```bash
ros2 launch spechemobot_bringup reactor_hall.launch.py headless:=true
ros2 action send_goal /process/run_batch spechemobot_msgs/action/RunBatch \
  "{batch_id: acceptance-1, target_temperature_c: 450.0, hold_time_s: 4.0, product_id: P-100}" --feedback
ros2 action send_goal /robot/pick_place spechemobot_msgs/action/PickPlace \
  "{container_id: C-001, robot_id: amr_1, source_location: conveyor, target_location: packaging, approach_height_m: 0.25}" --feedback
```

- [ ] `/process/state` publishes at approximately 10 Hz.
- [ ] Batch phases progress through heating, holding, and complete.
- [ ] `/robot/tasks` reports accepted, complete, and container identifiers.
- [ ] `ros2 topic pub --once /safety/estop std_msgs/msg/Bool "{data: true}"` aborts the batch.
- [ ] `ros2 service call /safety/reset std_srvs/srv/Trigger "{}"` clears the alarm and allows a new batch.

## Gate 7 - perception

```bash
ros2 run spechemobot_perception onnx_inference_node --ros-args \
  -p model_path:=/workspace/Spechemobot/models/spechemobot_thermal.onnx
ros2 topic echo /perception/thermal_reading --once
```

- [ ] The node subscribes to `/camera/image_raw` and `/thermal_camera`.
- [ ] Thermal `16UC1`, `32FC1`, and `8UC1` encodings are converted to Celsius.
- [ ] `/perception/thermal_reading` contains min, max, mean, hotspot, and over-temperature fields.
- [ ] With `SPECHEMOBOT_HAS_ORT`, the model loads and output names/shapes are validated.
- [ ] Without a model or ONNX Runtime, the thermal fallback still publishes.

## Gate 8 - datasets and evaluation

```bash
ros2 launch spechemobot_bringup reactor_hall.launch.py headless:=true \
  launch_recording:=true session_name:=acceptance-01
ros2 run spechemobot_dataset make_manifest \
  --root /workspace/Spechemobot/datasets/raw \
  --output /workspace/Spechemobot/datasets/processed/manifest.json
ros2 launch spechemobot_bringup reactor_hall.launch.py headless:=true \
  launch_eval:=true eval_duration_s:=30
```

- [ ] Each sample writes RGB/thermal files and a JSONL metadata record.
- [ ] The manifest has a deterministic train/validation split.
- [ ] The evaluation JSON reports topic rates and accepts or rejects the run against configured gates.

## Gate 9 - O3DE

```bash
docker compose --profile o3de-jazzy up -d
docker compose exec o3de-jazzy bash -lc '
  cd /workspace/Spechemobot
  bash scripts/v3_bootstrap_o3de.sh
  bash scripts/v3_build_o3de.sh
  test -x sim/o3de/SpechemobotO3DE/build/linux/bin/profile/SpechemobotO3DE.GameLauncher
'
```

- [ ] The project configures against `o3de-sdk` 26.05 without a source build.
- [ ] `SpechemobotO3DE.GameLauncher` builds.
- [ ] The launcher starts with `-rhi=null` and the `Spechemobot` level.
- [ ] ROS 2 gem components publish the same topic names as the Gazebo sensor rig.

## Gate 10 - Ruby orchestration

```bash
ruby orchestration/ruby/test/ros2_cli_test.rb
ruby orchestration/ruby/test/orchestrator_test.rb
orchestration/ruby/bin/spechemobot-orchestrator health
orchestration/ruby/bin/spechemobot-orchestrator batch --target 425 --hold 4
```

- [ ] Unit tests pass on Ruby 3.2 or newer.
- [ ] `health` reports all required nodes present during a live simulation.
- [ ] `batch` prints a JSON result and exits non-zero on a failed action.
- [ ] The HTTP server returns JSON for `/health`, `/state`, `/batch`, `/pick`, `/estop`, and `/reset`.
- [ ] The documentation states that Ruby is not on the safety path.
