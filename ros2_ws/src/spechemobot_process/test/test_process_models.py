import unittest

import rclpy
from rclpy.action import GoalResponse
from std_msgs.msg import Bool

from spechemobot_msgs.action import RunBatch
from spechemobot_msgs.msg import ProcessState
from spechemobot_process.container_manager_node import ContainerManagerNode
from spechemobot_process.safety_monitor_node import SafetyMonitorNode
from spechemobot_process.tep_replay_node import TepReplayNode


def process_state(temperature=25.0, pressure=101.3, level=50.0, stop=False):
    state = ProcessState()
    state.batch_id = "batch-test"
    state.phase = "holding"
    state.reactor_temperature_c = temperature
    state.reactor_pressure_kpa = pressure
    state.reactor_level_percent = level
    state.furnace_temperature_c = temperature
    state.emergency_stop = stop
    return state


class ProcessModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_container_manager_fills_active_container(self):
        node = ContainerManagerNode()
        try:
            node.on_state(process_state(temperature=300.0, level=60.0))
            node.publish()
            active = node.containers["C-003"]
            self.assertAlmostEqual(active["fill"], 70.0)
            self.assertAlmostEqual(active["temperature"], 121.25)
            self.assertTrue(active["hot"])
            self.assertTrue(active["attached"])
            self.assertFalse(active["defect"])
        finally:
            node.destroy_node()

    def test_container_manager_drains_when_idle(self):
        node = ContainerManagerNode()
        try:
            node.on_state(process_state(temperature=300.0, level=60.0))
            node.publish()
            fill = node.containers["C-003"]["fill"]
            node.phase = "idle"
            node.publish()
            self.assertLess(node.containers["C-003"]["fill"], fill)
        finally:
            node.destroy_node()

    def test_safety_monitor_latches_and_resets(self):
        node = SafetyMonitorNode()
        try:
            node.on_state(process_state(temperature=750.0))
            self.assertIn("TEMP_HIGH", node.latched)
            self.assertTrue(node.estop)

            node.on_state(process_state(temperature=500.0))
            self.assertNotIn("TEMP_HIGH", node.latched)

            node.on_state(process_state(temperature=500.0, stop=True))
            self.assertIn("ESTOP", node.latched)

            from std_srvs.srv import Trigger
            response = Trigger.Response()
            node.on_reset(Trigger.Request(), response)
            self.assertTrue(response.success)
            self.assertFalse(node.estop)
            self.assertEqual(node.latched, {})
        finally:
            node.destroy_node()

    def test_tep_rejects_invalid_goal_and_handles_estop(self):
        node = TepReplayNode()
        try:
            goal = RunBatch.Goal()
            goal.target_temperature_c = node.ambient
            self.assertEqual(node.goal_callback(goal), GoalResponse.REJECT)

            goal.target_temperature_c = node.ambient + 100.0
            self.assertEqual(node.goal_callback(goal), GoalResponse.ACCEPT)

            node.batch_active = True
            self.assertEqual(node.goal_callback(goal), GoalResponse.REJECT)
            node.batch_active = False

            node.on_estop(Bool(data=True))
            self.assertTrue(node.emergency_stop)
            self.assertFalse(node.furnace_enabled)
            self.assertEqual(node.phase, "aborted")
            self.assertEqual(node.setpoint, node.ambient)
        finally:
            node.destroy_node()


if __name__ == "__main__":
    unittest.main()
