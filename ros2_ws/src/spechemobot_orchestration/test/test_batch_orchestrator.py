import unittest

import rclpy
from std_srvs.srv import Trigger

from spechemobot_msgs.msg import ContainerState, ProcessState
from spechemobot_orchestration.batch_orchestrator import (
    BatchOrchestrator,
    select_pick_candidate,
)


def container_state(container_id, fill):
    state = ContainerState()
    state.container_id = container_id
    state.fill_percent = fill
    return state


class BatchOrchestratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_select_pick_candidate(self):
        containers = [
            container_state("C-001", 20.0),
            container_state("C-002", 80.0),
            container_state("C-003", 40.0),
            container_state("C-004", 60.0),
        ]
        selected = select_pick_candidate(containers)
        self.assertEqual(selected.container_id, "C-002")
        self.assertIsNone(select_pick_candidate([container_state("C-001", 10.0)]))

    def test_container_tracking_and_busy_reset(self):
        node = BatchOrchestrator()
        try:
            node.on_container(container_state("C-001", 55.0))
            self.assertEqual(node.containers["C-001"].fill_percent, 55.0)

            node.busy = True
            response = Trigger.Response()
            node.on_start(Trigger.Request(), response)
            self.assertFalse(response.success)
            self.assertIn("busy", response.message)

            state = ProcessState()
            state.phase = "complete"
            node.on_process(state)
            self.assertFalse(node.busy)
        finally:
            node.destroy_node()


if __name__ == "__main__":
    unittest.main()
