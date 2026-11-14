import math
import time
import uuid

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_msgs.msg import Bool

from spechemobot_msgs.action import RunBatch
from spechemobot_msgs.msg import FurnaceCommand, ProcessState, SafetyAlarm


class TepReplayNode(Node):
    def __init__(self):
        super().__init__("tep_replay_node")

        self.declare_parameter("publish_rate_hz", 10.0)
        self.declare_parameter("ambient_temperature_c", 25.0)
        self.declare_parameter("max_heater_power_kw", 160.0)
        self.declare_parameter("heater_gain_kw_per_k", 9.0)
        self.declare_parameter("heat_capacity_kj_per_k", 450.0)
        self.declare_parameter("heat_loss_kw_per_k", 0.08)
        self.declare_parameter("time_scale", 15.0)
        self.declare_parameter("max_heat_time_s", 120.0)
        self.declare_parameter("max_cool_time_s", 120.0)
        self.declare_parameter("default_target_temperature_c", 450.0)

        self.rate = float(self.get_parameter("publish_rate_hz").value)
        self.ambient = float(self.get_parameter("ambient_temperature_c").value)
        self.max_power = float(self.get_parameter("max_heater_power_kw").value)
        self.heater_gain = float(self.get_parameter("heater_gain_kw_per_k").value)
        self.heat_capacity = float(self.get_parameter("heat_capacity_kj_per_k").value)
        self.heat_loss = float(self.get_parameter("heat_loss_kw_per_k").value)
        self.time_scale = float(self.get_parameter("time_scale").value)
        self.max_heat_time = float(self.get_parameter("max_heat_time_s").value)
        self.max_cool_time = float(self.get_parameter("max_cool_time_s").value)
        self.default_target = float(self.get_parameter("default_target_temperature_c").value)

        self.batch_id = "batch-idle"
        self.phase = "idle"
        self.reactor_temperature = self.ambient
        self.furnace_temperature = self.ambient
        self.setpoint = self.ambient
        self.heater_power = 0.0
        self.level = 20.0
        self.feed_flow = 0.0
        self.product_flow = 0.0
        self.progress = 0.0
        self.emergency_stop = False
        self.furnace_enabled = False
        self.batch_active = False
        self.active_faults = []

        self.state_pub = self.create_publisher(ProcessState, "/process/state", 10)
        self.estop_pub = self.create_publisher(Bool, "/process/emergency_stop", 10)
        self.create_subscription(FurnaceCommand, "/furnace/command", self.on_furnace_command, 10)
        self.create_subscription(Bool, "/safety/estop", self.on_estop, 10)
        self.create_subscription(SafetyAlarm, "/safety/alarm", self.on_alarm, 10)

        self.action_group = ReentrantCallbackGroup()
        self.action_server = ActionServer(
            self,
            RunBatch,
            "/process/run_batch",
            execute_callback=self.execute_batch,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=self.action_group,
        )
        self.timer = self.create_timer(1.0 / self.rate, self.tick, callback_group=self.action_group)
        self.get_logger().info("TEP process replay ready")

    def goal_callback(self, goal_request):
        if self.batch_active:
            self.get_logger().warning("Rejecting batch: another batch is active")
            return GoalResponse.REJECT
        if goal_request.target_temperature_c <= self.ambient:
            self.get_logger().warning("Rejecting batch: target temperature must exceed ambient")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info("Batch cancel requested")
        return CancelResponse.ACCEPT

    def on_furnace_command(self, msg):
        self.setpoint = float(msg.target_temperature_c)
        self.furnace_enabled = bool(msg.enable)
        self.emergency_stop = bool(msg.emergency_stop) or self.emergency_stop
        if self.emergency_stop:
            self.phase = "aborted"
            self.furnace_enabled = False
            self.setpoint = self.ambient

    def on_estop(self, msg):
        if msg.data:
            self.emergency_stop = True
            self.furnace_enabled = False
            self.setpoint = self.ambient
            self.phase = "aborted"
            self.get_logger().error("Emergency stop engaged")

    def on_alarm(self, msg):
        if msg.severity in ("warning", "critical") and msg.alarm_id not in self.active_faults:
            self.active_faults.append(msg.alarm_id)
            self.active_faults = self.active_faults[-8:]
            if msg.severity == "critical":
                self.emergency_stop = True
                self.furnace_enabled = False
                self.setpoint = self.ambient
                self.phase = "aborted"

    def tick(self):
        dt = (1.0 / self.rate) * self.time_scale

        if self.emergency_stop:
            self.heater_power = 0.0
            self.furnace_enabled = False
        elif self.furnace_enabled:
            error = self.setpoint - self.furnace_temperature
            self.heater_power = max(0.0, min(self.max_power, self.heater_gain * error))
        else:
            self.heater_power = 0.0

        net_power = self.heater_power - self.heat_loss * (self.furnace_temperature - self.ambient)
        self.furnace_temperature += net_power * dt / self.heat_capacity
        self.furnace_temperature = max(self.ambient, self.furnace_temperature)

        lag = min(1.0, 0.08 * dt)
        self.reactor_temperature += (self.furnace_temperature - self.reactor_temperature) * lag

        if self.batch_active:
            self.level = 30.0 + 60.0 * min(1.0, max(0.0, self.progress))
            self.feed_flow = 0.42 if self.phase in ("heating", "holding") else 0.0
            self.product_flow = 0.28 if self.phase == "holding" else 0.0
        else:
            self.level += (20.0 - self.level) * min(1.0, 0.2 * dt)
            self.feed_flow = 0.0
            self.product_flow = 0.0

        if not self.batch_active and not self.emergency_stop and self.phase != "aborted":
            self.phase = "idle"

        self.publish_state()

    def publish_state(self):
        msg = ProcessState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "process"
        msg.batch_id = self.batch_id
        msg.phase = self.phase
        msg.reactor_temperature_c = float(self.reactor_temperature)
        msg.reactor_pressure_kpa = float(101.3 + max(0.0, self.reactor_temperature - 100.0) * 0.55 + self.level * 0.02)
        msg.reactor_level_percent = float(self.level)
        msg.feed_flow_kg_s = float(self.feed_flow)
        msg.product_flow_kg_s = float(self.product_flow)
        msg.furnace_temperature_c = float(self.furnace_temperature)
        msg.furnace_setpoint_c = float(self.setpoint)
        msg.heater_power_kw = float(self.heater_power)
        msg.interlock_active = bool(self.emergency_stop)
        msg.emergency_stop = bool(self.emergency_stop)
        msg.active_faults = list(self.active_faults)
        self.state_pub.publish(msg)

        stop = Bool()
        stop.data = bool(self.emergency_stop)
        self.estop_pub.publish(stop)

    def feedback(self, goal_handle):
        fb = RunBatch.Feedback()
        fb.phase = self.phase
        fb.progress = float(self.progress)
        fb.current_temperature_c = float(self.reactor_temperature)
        goal_handle.publish_feedback(fb)

    def finish(self, goal_handle, success, message, duration):
        self.batch_active = False
        self.furnace_enabled = False
        self.setpoint = self.ambient
        self.phase = "complete" if success else "aborted"
        result = RunBatch.Result()
        result.success = bool(success)
        result.message = message
        result.max_temperature_c = float(self.furnace_temperature)
        result.duration_s = float(duration)
        if success:
            goal_handle.succeed()
        elif goal_handle.is_cancel_requested:
            goal_handle.canceled()
        else:
            goal_handle.abort()
        return result

    def execute_batch(self, goal_handle):
        goal = goal_handle.request
        started = time.monotonic()
        self.batch_id = goal.batch_id or f"batch-{uuid.uuid4().hex[:8]}"
        target = float(goal.target_temperature_c)
        hold_time = max(0.0, float(goal.hold_time_s))
        self.batch_active = True
        self.emergency_stop = False
        self.phase = "heating"
        self.setpoint = target
        self.furnace_enabled = True
        self.progress = 0.0
        self.get_logger().info(f"Starting {self.batch_id} target={target:.1f}C hold={hold_time:.1f}s")

        while self.reactor_temperature < target - 2.0:
            if goal_handle.is_cancel_requested:
                return self.finish(goal_handle, False, "batch canceled during heating", time.monotonic() - started)
            if self.emergency_stop:
                return self.finish(goal_handle, False, "emergency stop during heating", time.monotonic() - started)
            if time.monotonic() - started > self.max_heat_time:
                return self.finish(goal_handle, False, "heating timeout", time.monotonic() - started)
            self.progress = max(0.0, min(0.55, 0.55 * (self.reactor_temperature - self.ambient) / max(1.0, target - self.ambient)))
            self.feedback(goal_handle)
            time.sleep(0.1)

        self.phase = "holding"
        hold_started = time.monotonic()
        while time.monotonic() - hold_started < hold_time:
            if goal_handle.is_cancel_requested:
                return self.finish(goal_handle, False, "batch canceled during hold", time.monotonic() - started)
            if self.emergency_stop:
                return self.finish(goal_handle, False, "emergency stop during hold", time.monotonic() - started)
            self.progress = min(0.9, 0.55 + 0.35 * (time.monotonic() - hold_started) / max(0.1, hold_time))
            self.feedback(goal_handle)
            time.sleep(0.1)

        self.phase = "cooling"
        self.furnace_enabled = False
        self.setpoint = self.ambient
        cool_started = time.monotonic()
        while self.reactor_temperature > self.ambient + 20.0:
            if goal_handle.is_cancel_requested:
                return self.finish(goal_handle, False, "batch canceled during cooling", time.monotonic() - started)
            if time.monotonic() - cool_started > self.max_cool_time:
                break
            self.progress = min(0.98, 0.9 + 0.08 * (1.0 - (self.reactor_temperature - self.ambient) / max(1.0, target)))
            self.feedback(goal_handle)
            time.sleep(0.1)

        self.progress = 1.0
        self.feedback(goal_handle)
        return self.finish(goal_handle, True, "batch complete", time.monotonic() - started)


def main(args=None):
    rclpy.init(args=args)
    node = TepReplayNode()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
