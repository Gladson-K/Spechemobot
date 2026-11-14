# O3DE simulation project

`SpechemobotO3DE` is a minimal O3DE project scaffold for the O3DE SDK installed by `deployment/docker-v3/sim-o3de/Dockerfile`.

The project uses:

- Engine `o3de-sdk` from `/opt/O3DE/26.05`.
- Gems `ROS2`, `ROS2Sensors`, `ROS2Controllers`, and `LevelGeoreferencing`.
- A single project module so `SpechemobotO3DE.GameLauncher` can be built.
- An empty `Spechemobot` level with a directional light. Populate it in the O3DE Editor with the chemical plant and sensor rig assets.

## Bootstrap

Inside the O3DE container:

```bash
bash scripts/v3_bootstrap_o3de.sh
```

This registers the SDK engine, the project, the o3de-extras gems/templates, and writes `user/project.json` with the local engine path.

## Build

```bash
bash scripts/v3_build_o3de.sh
```

The launcher is written to:

```text
sim/o3de/SpechemobotO3DE/build/linux/bin/profile/SpechemobotO3DE.GameLauncher
```

## Launch with ROS 2

The ROS 2 bringup can start the launcher without Gazebo:

```bash
ros2 launch spechemobot_bringup sim.launch.py sim_backend:=o3de world:=reactor_hall
```

Set `O3DE_RHI=null` for headless CI. The O3DE level must contain the ROS 2 sensors and the plant entities before the bridge topics match the Gazebo worlds.

## World mapping

The Gazebo worlds under `sim/gazebo/worlds/` are the reference layouts:

| Gazebo world | O3DE level to create |
| --- | --- |
| `reactor_hall.sdf` | `Levels/ReactorHall` |
| `furnace_annealing.sdf` | `Levels/FurnaceAnnealing` |
| `conveyor_sorting.sdf` | `Levels/ConveyorSorting` |
| `sensor_qualification.sdf` | `Levels/SensorQualification` |

O3DE does not consume SDF. Rebuild these layouts in the O3DE Editor, attach the ROS 2 camera/lidar/IMU components, and keep the topic names aligned with `ros2_ws/src/spechemobot_bringup/config/gz_bridge.yaml`.
