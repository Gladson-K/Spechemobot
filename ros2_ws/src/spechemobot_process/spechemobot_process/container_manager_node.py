import rclpy
from rclpy.node import Node

from spechemobot_msgs.msg import ContainerState, ProcessState, ThermalReading


def container_topic(container_id):
    return f"/containers/{container_id.replace('-', '_')}/state"


class ContainerManagerNode(Node):
    def __init__(self):
        super().__init__("container_manager_node")
        self.declare_parameter("container_count", 4)
        self.declare_parameter("publish_rate_hz", 1.0)
        self.declare_parameter("hot_threshold_c", 120.0)

        self.count = int(self.get_parameter("container_count").value)
        self.rate = float(self.get_parameter("publish_rate_hz").value)
        self.hot_threshold = float(self.get_parameter("hot_threshold_c").value)
        self.phase = "idle"
        self.batch_id = "batch-idle"
        self.furnace_temperature = 25.0
        self.level = 20.0
        self.hotspot = 25.0
        self.containers = {}

        for index in range(self.count):
            container_id = f"C-{index + 1:03d}"
            self.containers[container_id] = {
                "product": "unassigned",
                "location": "conveyor",
                "fill": 0.0,
                "mass": 0.0,
                "temperature": 25.0,
                "hot": False,
                "attached": False,
                "defect": False,
            }

        self.container_publishers = {
            container_id: self.create_publisher(ContainerState, container_topic(container_id), 10)
            for container_id in self.containers
        }
        self.create_subscription(ProcessState, "/process/state", self.on_state, 10)
        self.create_subscription(ThermalReading, "/furnace/thermal_reading", self.on_thermal, 10)
        self.create_timer(1.0 / self.rate, self.publish)

    def on_state(self, msg):
        self.phase = msg.phase
        self.batch_id = msg.batch_id
        self.furnace_temperature = float(msg.furnace_temperature_c)
        self.level = float(msg.reactor_level_percent)

    def on_thermal(self, msg):
        self.hotspot = float(msg.max_temperature_c)

    def publish(self):
        stamp = self.get_clock().now().to_msg()
        active_index = 0
        if self.phase in ("holding", "complete"):
            active_index = min(self.count - 1, int(self.level / 25.0))

        for index, (container_id, container) in enumerate(self.containers.items()):
            if index == active_index and self.phase in ("holding", "complete"):
                container["product"] = "P-100" if self.phase == "holding" else "P-100-batch"
                container["fill"] = min(95.0, 40.0 + self.level * 0.5)
                container["mass"] = 2.0 + container["fill"] * 0.08
                container["temperature"] = 0.35 * self.furnace_temperature + 0.65 * self.hotspot
            else:
                container["fill"] = max(0.0, container["fill"] - 0.2)
                container["mass"] = max(0.0, container["mass"] - 0.02)
                container["temperature"] = max(25.0, container["temperature"] - 0.5)
                if container["fill"] <= 0.1:
                    container["product"] = "empty"

            container["hot"] = container["temperature"] > self.hot_threshold
            container["attached"] = container["fill"] > 5.0
            container["defect"] = container["temperature"] > 750.0

            msg = ContainerState()
            msg.header.stamp = stamp
            msg.header.frame_id = "conveyor"
            msg.container_id = container_id
            msg.product_id = container["product"]
            msg.location = container["location"]
            msg.fill_percent = float(container["fill"])
            msg.mass_kg = float(container["mass"])
            msg.temperature_c = float(container["temperature"])
            msg.hot = bool(container["hot"])
            msg.attached = bool(container["attached"])
            msg.defect_detected = bool(container["defect"])
            self.container_publishers[container_id].publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ContainerManagerNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
