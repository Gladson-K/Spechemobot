import json
import tempfile
import time
import unittest
from pathlib import Path

import rclpy

from spechemobot_eval.evaluate_run import EvaluateRun
from spechemobot_msgs.msg import ContainerState, ProcessState, ThermalReading


class EvaluateRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_stats_and_report(self):
        node = EvaluateRun()
        temp_dir = tempfile.TemporaryDirectory()
        try:
            node.started = time.monotonic() - 1.0
            node.output_file = Path(temp_dir.name) / "eval.json"

            for index in range(10):
                state = ProcessState()
                state.phase = "holding"
                state.reactor_temperature_c = 300.0 + index
                state.furnace_temperature_c = 450.0 + index
                node.on_process(state)

            for index in range(6):
                reading = ThermalReading()
                reading.max_temperature_c = 470.0 + index
                reading.mean_temperature_c = 440.0 + index
                node.on_perception(reading)

            container = ContainerState()
            container.container_id = "C-001"
            container.fill_percent = 75.0
            container.mass_kg = 8.0
            container.temperature_c = 120.0
            container.hot = True
            node.on_container(container)

            report = node.write_report()
            persisted = json.loads(node.output_file.read_text(encoding="utf-8"))

            self.assertEqual(report["counts"]["process"], 10)
            self.assertEqual(report["counts"]["perception"], 6)
            self.assertEqual(report["phases"], {"holding": 10})
            self.assertEqual(report["reactor_temperature_c"]["count"], 10)
            self.assertAlmostEqual(report["reactor_temperature_c"]["mean"], 304.5)
            self.assertEqual(report["containers"]["C-001"]["fill_percent"], 75.0)
            self.assertTrue(report["gates"]["process_rate"])
            self.assertTrue(report["gates"]["perception_rate"])
            self.assertTrue(report["passed"])
            self.assertEqual(persisted["counts"], report["counts"])

            node.min_process_rate = 1000.0
            self.assertFalse(node.build_report()["gates"]["process_rate"])
            self.assertEqual(
                node.stats([]), {"min": None, "max": None, "mean": None, "count": 0})
        finally:
            node.destroy_node()
            temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
