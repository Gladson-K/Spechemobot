import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image

from spechemobot_msgs.msg import ProcessState, ThermalReading


class RecordDataset(Node):
    def __init__(self):
        super().__init__("record_dataset")
        self.declare_parameter("output_dir", "/workspace/Spechemobot/datasets/raw")
        self.declare_parameter("session_name", "")
        self.declare_parameter("capture_rate_hz", 2.0)
        self.declare_parameter("save_rgb", True)
        self.declare_parameter("save_thermal", True)
        self.declare_parameter("max_samples", 0)

        output_dir = Path(self.get_parameter("output_dir").value)
        session = self.get_parameter("session_name").value
        if not session:
            session = datetime.now(timezone.utc).strftime("session-%Y%m%dT%H%M%SZ")
        self.session_dir = output_dir / session
        self.rgb_dir = self.session_dir / "rgb"
        self.thermal_dir = self.session_dir / "thermal"
        self.rgb_dir.mkdir(parents=True, exist_ok=True)
        self.thermal_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_path = self.session_dir / "metadata.jsonl"
        self.metadata_file = self.metadata_path.open("a", encoding="utf-8")

        self.rate = float(self.get_parameter("capture_rate_hz").value)
        self.save_rgb = bool(self.get_parameter("save_rgb").value)
        self.save_thermal = bool(self.get_parameter("save_thermal").value)
        self.max_samples = int(self.get_parameter("max_samples").value)
        self.samples = 0
        self.bridge = CvBridge()
        self.rgb = None
        self.thermal = None
        self.process = None
        self.perception = None

        self.create_subscription(Image, "/camera/image_raw", self.on_rgb, 10)
        self.create_subscription(Image, "/thermal_camera", self.on_thermal, 10)
        self.create_subscription(ProcessState, "/process/state", self.on_process, 10)
        self.create_subscription(ThermalReading, "/perception/thermal_reading", self.on_perception, 10)
        self.create_timer(1.0 / self.rate, self.capture)
        self.get_logger().info(f"Recording dataset to {self.session_dir}")

    def on_rgb(self, msg):
        self.rgb = msg

    def on_thermal(self, msg):
        self.thermal = msg

    def on_process(self, msg):
        self.process = msg

    def on_perception(self, msg):
        self.perception = msg

    def capture(self):
        if self.max_samples and self.samples >= self.max_samples:
            return
        if self.rgb is None and self.thermal is None:
            return

        sample_id = f"{self.samples:06d}-{uuid.uuid4().hex[:6]}"
        record = {
            "sample_id": sample_id,
            "captured_at": time.time(),
            "rgb": None,
            "thermal": None,
            "thermal_stats": None,
            "process": None,
            "perception": None,
        }

        if self.save_rgb and self.rgb is not None:
            try:
                image = self.bridge.imgmsg_to_cv2(self.rgb, desired_encoding="passthrough")
                if image.dtype != np.uint8:
                    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                if image.ndim == 2:
                    image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                path = self.rgb_dir / f"{sample_id}.png"
                cv2.imwrite(str(path), image)
                record["rgb"] = str(path.relative_to(self.session_dir))
            except Exception as error:
                self.get_logger().warning(f"RGB capture failed: {error}")

        if self.save_thermal and self.thermal is not None:
            try:
                image = self.bridge.imgmsg_to_cv2(self.thermal, desired_encoding="passthrough")
                if image.dtype == np.float32:
                    stats = {
                        "min": float(np.nanmin(image)),
                        "max": float(np.nanmax(image)),
                        "mean": float(np.nanmean(image)),
                    }
                    image = cv2.normalize(image, None, 0, 65535, cv2.NORM_MINMAX).astype(np.uint16)
                    record["thermal_stats"] = stats
                elif image.dtype == np.uint8:
                    image = image.astype(np.uint16) * 257
                path = self.thermal_dir / f"{sample_id}.png"
                cv2.imwrite(str(path), image)
                record["thermal"] = str(path.relative_to(self.session_dir))
            except Exception as error:
                self.get_logger().warning(f"Thermal capture failed: {error}")

        if self.process is not None:
            record["process"] = {
                "batch_id": self.process.batch_id,
                "phase": self.process.phase,
                "reactor_temperature_c": self.process.reactor_temperature_c,
                "reactor_pressure_kpa": self.process.reactor_pressure_kpa,
                "reactor_level_percent": self.process.reactor_level_percent,
                "furnace_temperature_c": self.process.furnace_temperature_c,
                "heater_power_kw": self.process.heater_power_kw,
                "emergency_stop": self.process.emergency_stop,
            }

        if self.perception is not None:
            record["perception"] = {
                "sensor_id": self.perception.sensor_id,
                "min_temperature_c": self.perception.min_temperature_c,
                "max_temperature_c": self.perception.max_temperature_c,
                "mean_temperature_c": self.perception.mean_temperature_c,
                "over_temperature": self.perception.over_temperature,
            }

        self.metadata_file.write(json.dumps(record) + "\n")
        self.metadata_file.flush()
        self.samples += 1
        if self.samples % 20 == 0:
            self.get_logger().info(f"Captured {self.samples} samples")

    def destroy_node(self):
        if hasattr(self, "metadata_file"):
            self.metadata_file.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RecordDataset()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
