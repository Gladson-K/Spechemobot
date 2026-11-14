import uuid

import rclpy
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Trigger

from spechemobot_msgs.action import PickPlace, RunBatch
from spechemobot_msgs.msg import ContainerState, ProcessState


def container_topic(container_id):
    return f"/containers/{container_id.replace('-', '_')}/state"


def select_pick_candidate(containers, min_fill_percent=40.0):
    candidates = [container for container in containers if container.fill_percent > min_fill_percent]
    if not candidates:
        return None
    return max(candidates, key=lambda container: container.fill_percent)


class BatchOrchestrator(Node):
    def __init__(self):
        super().__init__("batch_orchestrator")
        self.declare_parameter("target_temperature_c", 450.0)
        self.declare_parameter("hold_time_s", 8.0)
        self.declare_parameter("product_id", "P-100")
        self.declare_parameter("auto_start", False)
        self.declare_parameter("auto_start_delay_s", 10.0)
        self.declare_parameter("auto_pick", True)

        self.target = float(self.get_parameter("target_temperature_c").value)
        self.hold_time = float(self.get_parameter("hold_time_s").value)
        self.product_id = str(self.get_parameter("product_id").value)
        self.auto_pick = bool(self.get_parameter("auto_pick").value)
        self.busy = False
        self.containers = {}
        self.group = ReentrantCallbackGroup()

        self.run_client = ActionClient(self, RunBatch, "/process/run_batch", callback_group=self.group)
        self.pick_client = ActionClient(self, PickPlace, "/robot/pick_place", callback_group=self.group)
        for index in range(1, 5):
            self.create_subscription(
                ContainerState, container_topic(f"C-{index:03d}"), self.on_container, 10)
        self.create_subscription(ProcessState, "/process/state", self.on_process, 10)
        self.create_service(Trigger, "/orchestrator/start_batch", self.on_start)

        if bool(self.get_parameter("auto_start").value):
            delay = float(self.get_parameter("auto_start_delay_s").value)
            self.create_timer(delay, self.auto_start, callback_group=self.group)

        self.get_logger().info("Batch orchestrator ready on /orchestrator/start_batch")

    def on_container(self, msg):
        self.containers[msg.container_id] = msg

    def on_process(self, msg):
        if msg.phase == "complete":
            self.busy = False

    def auto_start(self):
        if not self.busy:
            self.start_batch()

    def on_start(self, request, response):
        if self.busy:
            response.success = False
            response.message = "orchestrator busy"
            return response
        self.start_batch()
        response.success = True
        response.message = "batch submitted"
        return response

    def start_batch(self):
        if not self.run_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().error("RunBatch action server unavailable")
            return
        self.busy = True
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"
        goal = RunBatch.Goal()
        goal.batch_id = batch_id
        goal.target_temperature_c = self.target
        goal.hold_time_s = self.hold_time
        goal.product_id = self.product_id
        self.get_logger().info(f"Submitting {batch_id} target={self.target:.1f}C hold={self.hold_time:.1f}s")
        future = self.run_client.send_goal_async(goal, feedback_callback=self.on_feedback)
        future.add_done_callback(self.on_goal_response)

    def on_feedback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().debug(
            f"batch phase={feedback.phase} progress={feedback.progress:.2f} temp={feedback.current_temperature_c:.1f}C")

    def on_goal_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Batch goal rejected")
            self.busy = False
            return
        self.get_logger().info("Batch goal accepted")
        goal_handle.get_result_async().add_done_callback(self.on_batch_result)

    def on_batch_result(self, future):
        result = future.result().result
        self.get_logger().info(f"Batch result success={result.success} message={result.message}")
        if result.success and self.auto_pick:
            candidate = select_pick_candidate(self.containers.values())
            if candidate is not None:
                self.send_pick(candidate)
                return
        self.busy = False

    def send_pick(self, container):
        if not self.pick_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warning("PickPlace action server unavailable")
            self.busy = False
            return
        goal = PickPlace.Goal()
        goal.container_id = container.container_id
        goal.robot_id = "amr_1"
        goal.source_location = "conveyor"
        goal.target_location = "packaging"
        goal.approach_height_m = 0.25
        self.get_logger().info(f"Dispatching pick for {container.container_id}")
        future = self.pick_client.send_goal_async(goal)
        future.add_done_callback(self.on_pick_response)

    def on_pick_response(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.busy = False
            return
        goal_handle.get_result_async().add_done_callback(self.on_pick_result)

    def on_pick_result(self, future):
        result = future.result().result
        self.get_logger().info(f"Pick result success={result.success} message={result.message}")
        self.busy = False


def main(args=None):
    rclpy.init(args=args)
    node = BatchOrchestrator()
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
