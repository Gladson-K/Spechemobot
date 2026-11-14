import random

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Temperature

from spechemobot_msgs.msg import ProcessState, ThermalReading


class FurnaceModelNode(Node):
    def __init__(self):
        super().__init__("furnace_model_node")
        self.declare_parameter("publish_rate_hz", 5.0)
        self.declare_parameter("skin_offset_c", 12.0)
        self.declare_parameter("hotspot_bias", 1.05)
        self.declare_parameter("noise_c", 1.5)

        self.rate = float(self.get_parameter("publish_rate_hz").value)
        self.skin_offset = float(self.get_parameter("skin_offset_c").value)
        self.hotspot_bias = float(self.get_parameter("hotspot_bias").value)
        self.noise = float(self.get_parameter("noise_c").value)

        self.temperature = 25.0
        self.batch_id = "batch-idle"
        self.over_temperature = False

        self.temp_pub = self.create_publisher(Temperature, "/furnace/skin_temperature", 10)
        self.thermal_pub = self.create_publisher(ThermalReading, "/furnace/thermal_reading", 10)
        self.create_subscription(ProcessState, "/process/state", self.on_state, 10)
        self.create_timer(1.0 / self.rate, self.publish)

    def on_state(self, msg):
        self.temperature = float(msg.furnace_temperature_c)
        self.batch_id = msg.batch_id
        self.over_temperature = msg.furnace_temperature_c > 700.0

    def publish(self):
        stamp = self.get_clock().now().to_msg()
        skin = self.temperature + self.skin_offset + random.uniform(-self.noise, self.noise)

        temp = Temperature()
        temp.header.stamp = stamp
        temp.header.frame_id = "furnace"
        temp.temperature = float(skin)
        temp.variance = float(self.noise * self.noise)
        self.temp_pub.publish(temp)

        thermal = ThermalReading()
        thermal.header.stamp = stamp
        thermal.header.frame_id = "furnace"
        thermal.sensor_id = "furnace-thermal"
        thermal.min_temperature_c = float(self.temperature - 4.0)
        thermal.max_temperature_c = float(max(self.temperature, skin) * self.hotspot_bias)
        thermal.mean_temperature_c = float(0.7 * self.temperature + 0.3 * skin)
        thermal.hotspot_x = 0.62
        thermal.hotspot_y = 0.48
        thermal.over_temperature = bool(self.over_temperature)
        self.thermal_pub.publish(thermal)


def main(args=None):
    rclpy.init(args=args)
    node = FurnaceModelNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
