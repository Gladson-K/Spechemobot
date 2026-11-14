import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

from spechemobot_msgs.msg import ProcessState, SafetyAlarm, ThermalReading


class SafetyMonitorNode(Node):
    def __init__(self):
        super().__init__("safety_monitor_node")
        self.declare_parameter("max_temperature_c", 700.0)
        self.declare_parameter("max_pressure_kpa", 480.0)
        self.declare_parameter("min_level_percent", 5.0)
        self.declare_parameter("max_thermal_c", 720.0)

        self.max_temperature = float(self.get_parameter("max_temperature_c").value)
        self.max_pressure = float(self.get_parameter("max_pressure_kpa").value)
        self.min_level = float(self.get_parameter("min_level_percent").value)
        self.max_thermal = float(self.get_parameter("max_thermal_c").value)

        self.latched = {}
        self.estop = False
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)

        self.alarm_pub = self.create_publisher(SafetyAlarm, "/safety/alarm", qos)
        self.estop_pub = self.create_publisher(Bool, "/safety/estop", qos)
        self.interlock_pub = self.create_publisher(Bool, "/safety/interlock", qos)
        self.create_subscription(ProcessState, "/process/state", self.on_state, 10)
        self.create_subscription(ThermalReading, "/furnace/thermal_reading", self.on_thermal, 10)
        self.create_service(Trigger, "/safety/reset", self.on_reset)

    def raise_alarm(self, alarm_id, severity, source, message, value, limit):
        previous = self.latched.get(alarm_id)
        if previous == severity:
            return
        alarm = SafetyAlarm()
        alarm.header.stamp = self.get_clock().now().to_msg()
        alarm.header.frame_id = "safety"
        alarm.alarm_id = alarm_id
        alarm.severity = severity
        alarm.source = source
        alarm.message = message
        alarm.value = float(value)
        alarm.limit = float(limit)
        alarm.acknowledged = False
        self.latched[alarm_id] = severity
        self.alarm_pub.publish(alarm)
        self.get_logger().warning(f"{severity.upper()} {alarm_id}: {message} ({value:.2f} / {limit:.2f})")
        if severity == "critical":
            self.estop = True
            stop = Bool()
            stop.data = True
            self.estop_pub.publish(stop)
            interlock = Bool()
            interlock.data = True
            self.interlock_pub.publish(interlock)

    def clear_alarm(self, alarm_id):
        if alarm_id in self.latched:
            self.latched.pop(alarm_id)
            alarm = SafetyAlarm()
            alarm.header.stamp = self.get_clock().now().to_msg()
            alarm.header.frame_id = "safety"
            alarm.alarm_id = alarm_id
            alarm.severity = "cleared"
            alarm.source = "safety_monitor"
            alarm.message = f"{alarm_id} cleared"
            alarm.acknowledged = True
            self.alarm_pub.publish(alarm)

    def on_state(self, msg):
        if msg.furnace_temperature_c > self.max_temperature:
            self.raise_alarm("TEMP_HIGH", "critical", "furnace", "Furnace temperature above limit", msg.furnace_temperature_c, self.max_temperature)
        else:
            self.clear_alarm("TEMP_HIGH")

        if msg.reactor_pressure_kpa > self.max_pressure:
            self.raise_alarm("PRESSURE_HIGH", "critical", "reactor", "Reactor pressure above limit", msg.reactor_pressure_kpa, self.max_pressure)
        else:
            self.clear_alarm("PRESSURE_HIGH")

        if msg.reactor_level_percent < self.min_level:
            self.raise_alarm("LEVEL_LOW", "warning", "reactor", "Reactor level below limit", msg.reactor_level_percent, self.min_level)
        else:
            self.clear_alarm("LEVEL_LOW")

        if msg.emergency_stop:
            self.raise_alarm("ESTOP", "critical", "process", "Emergency stop active", 1.0, 0.0)
        else:
            self.clear_alarm("ESTOP")

    def on_thermal(self, msg):
        if msg.max_temperature_c > self.max_thermal:
            self.raise_alarm("THERMAL_HIGH", "critical", "thermal_camera", "Thermal hotspot above limit", msg.max_temperature_c, self.max_thermal)
        else:
            self.clear_alarm("THERMAL_HIGH")

    def on_reset(self, request, response):
        self.estop = False
        self.latched.clear()
        interlock = Bool()
        interlock.data = False
        self.interlock_pub.publish(interlock)
        stop = Bool()
        stop.data = False
        self.estop_pub.publish(stop)
        response.success = True
        response.message = "safety interlocks cleared"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = SafetyMonitorNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
