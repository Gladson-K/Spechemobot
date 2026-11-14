import json
import time
from collections import Counter
from pathlib import Path

import rclpy
from rclpy.node import Node

from spechemobot_msgs.msg import ContainerState, ProcessState, RobotTask, SafetyAlarm, ThermalReading


class EvaluateRun(Node):
    def __init__(self):
        super().__init__("evaluate_run")
        self.declare_parameter("duration_s", 60.0)
        self.declare_parameter("output_file", "/workspace/Spechemobot/datasets/processed/eval.json")
        self.declare_parameter("min_process_rate_hz", 8.0)
        self.declare_parameter("min_perception_rate_hz", 5.0)
        self.duration = float(self.get_parameter("duration_s").value)
        self.output_file = Path(self.get_parameter("output_file").value)
        self.min_process_rate = float(self.get_parameter("min_process_rate_hz").value)
        self.min_perception_rate = float(self.get_parameter("min_perception_rate_hz").value)

        self.started = time.monotonic()
        self.counts = Counter()
        self.phases = Counter()
        self.alarms = Counter()
        self.severities = Counter()
        self.robot_states = Counter()
        self.reactor_temperatures = []
        self.furnace_temperatures = []
        self.thermal_max = []
        self.thermal_mean = []
        self.containers = {}

        self.create_subscription(ProcessState, "/process/state", self.on_process, 10)
        self.create_subscription(ThermalReading, "/perception/thermal_reading", self.on_perception, 10)
        self.create_subscription(ThermalReading, "/furnace/thermal_reading", self.on_furnace_thermal, 10)
        self.create_subscription(SafetyAlarm, "/safety/alarm", self.on_alarm, 10)
        self.create_subscription(RobotTask, "/robot/tasks", self.on_robot, 10)
        for index in range(1, 5):
            topic = f"/containers/C_{index:03d}/state"
            self.create_subscription(ContainerState, topic, self.on_container, 10)

        self.create_timer(self.duration, self.finish)
        self.get_logger().info(f"Evaluating for {self.duration:.1f}s")

    def on_process(self, msg):
        self.counts["process"] += 1
        self.phases[msg.phase] += 1
        self.reactor_temperatures.append(float(msg.reactor_temperature_c))
        self.furnace_temperatures.append(float(msg.furnace_temperature_c))

    def on_perception(self, msg):
        self.counts["perception"] += 1
        self.thermal_max.append(float(msg.max_temperature_c))
        self.thermal_mean.append(float(msg.mean_temperature_c))

    def on_furnace_thermal(self, msg):
        self.counts["furnace_thermal"] += 1

    def on_alarm(self, msg):
        self.counts["alarm"] += 1
        self.alarms[msg.alarm_id] += 1
        self.severities[msg.severity] += 1

    def on_robot(self, msg):
        self.counts["robot_task"] += 1
        self.robot_states[msg.state] += 1

    def on_container(self, msg):
        self.counts["container"] += 1
        self.containers[msg.container_id] = {
            "fill_percent": msg.fill_percent,
            "mass_kg": msg.mass_kg,
            "temperature_c": msg.temperature_c,
            "hot": msg.hot,
            "defect_detected": msg.defect_detected,
        }

    def rate(self, key):
        elapsed = max(0.001, time.monotonic() - self.started)
        return self.counts[key] / elapsed

    def stats(self, values):
        if not values:
            return {"min": None, "max": None, "mean": None, "count": 0}
        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "count": len(values),
        }

    def build_report(self):
        process_rate = self.rate("process")
        perception_rate = self.rate("perception")
        report = {
            "elapsed_s": time.monotonic() - self.started,
            "counts": dict(self.counts),
            "rates_hz": {
                "process": process_rate,
                "perception": perception_rate,
                "furnace_thermal": self.rate("furnace_thermal"),
                "robot_task": self.rate("robot_task"),
                "container": self.rate("container"),
            },
            "phases": dict(self.phases),
            "alarms": dict(self.alarms),
            "alarm_severities": dict(self.severities),
            "robot_task_states": dict(self.robot_states),
            "reactor_temperature_c": self.stats(self.reactor_temperatures),
            "furnace_temperature_c": self.stats(self.furnace_temperatures),
            "perception_max_temperature_c": self.stats(self.thermal_max),
            "perception_mean_temperature_c": self.stats(self.thermal_mean),
            "containers": self.containers,
            "gates": {
                "process_rate": process_rate >= self.min_process_rate,
                "perception_rate": perception_rate >= self.min_perception_rate,
            },
        }
        report["passed"] = all(report["gates"].values())
        return report

    def write_report(self):
        report = self.build_report()
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        self.get_logger().info(f"Evaluation written to {self.output_file}; passed={report['passed']}")
        return report

    def finish(self):
        self.write_report()
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = EvaluateRun()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
