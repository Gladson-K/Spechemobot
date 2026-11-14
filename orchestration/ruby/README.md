# Spechemobot Ruby orchestration (experimental)

A thin Ruby supervisor for the ROS 2 process, robot, and safety interfaces. It is intentionally experimental: it shells out to the `ros2` CLI instead of linking native ROS 2 bindings, so it is suitable for operator tooling and integration tests, not hard real-time control.

## Prerequisites

- ROS 2 Jazzy or Lyrical sourced (`source /opt/ros/$ROS_DISTRO/setup.bash`).
- The `ros2_ws` workspace built and sourced so `spechemobot_msgs/action/*` is available.
- A running simulation stack with `/process/run_batch`, `/robot/pick_place`, `/process/state`, and `/safety/reset`.

## CLI

```bash
orchestration/ruby/bin/spechemobot-orchestrator health
orchestration/ruby/bin/spechemobot-orchestrator state
orchestration/ruby/bin/spechemobot-orchestrator batch --target 425 --hold 6 --product P-200
orchestration/ruby/bin/spechemobot-orchestrator pick --container C-002
orchestration/ruby/bin/spechemobot-orchestrator estop
orchestration/ruby/bin/spechemobot-orchestrator reset
```

## HTTP API

```bash
orchestration/ruby/bin/spechemobot-orchestrator --http --host 127.0.0.1 --port 8090
```

| Method | Path | Body |
| --- | --- | --- |
| GET | `/health` | none |
| GET | `/state` | none |
| POST | `/batch` | `{"target_temperature_c":425,"hold_time_s":6,"product_id":"P-200"}` |
| POST | `/pick` | `{"container_id":"C-002","target_location":"packaging"}` |
| POST | `/estop` | `{"engage":true}` |
| POST | `/reset` | none |

Configure defaults in `config/orchestration.yaml`.

## Tests

```bash
ruby orchestration/ruby/test/ros2_cli_test.rb
ruby orchestration/ruby/test/orchestrator_test.rb
```

## Safety boundary

The E-stop path in this process is a convenience interface. Production safety must use a hardware E-stop and deterministic interlocks; do not make safety depend on Ruby, HTTP, or best-effort DDS delivery.
