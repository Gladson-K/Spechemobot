import importlib.util
import unittest
from pathlib import Path

from launch import LaunchDescription


LAUNCH_DIR = Path(__file__).resolve().parents[1] / "launch"


def load_launch_module(name):
    path = LAUNCH_DIR / f"{name}.launch.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LaunchTest(unittest.TestCase):
    def test_bool_value(self):
        module = load_launch_module("sim")
        for value in ("1", "true", "TRUE", "yes", "on"):
            self.assertTrue(module.bool_value(value))
        for value in ("0", "false", "no", "off", ""):
            self.assertFalse(module.bool_value(value))

    def test_sim_launch_description_builds(self):
        module = load_launch_module("sim")
        description = module.generate_launch_description()
        self.assertIsInstance(description, LaunchDescription)
        self.assertGreater(len(description.entities), 0)

    def test_world_launch_files_are_importable(self):
        for name in (
            "reactor_hall",
            "furnace_annealing",
            "conveyor_sorting",
            "sensor_qualification",
        ):
            module = load_launch_module(name)
            description = module.generate_launch_description()
            self.assertIsInstance(description, LaunchDescription)


if __name__ == "__main__":
    unittest.main()
