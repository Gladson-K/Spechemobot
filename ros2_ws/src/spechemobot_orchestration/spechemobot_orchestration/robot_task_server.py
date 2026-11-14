import time
import uuid

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node

from spechemobot_msgs.action import PickPlace
from spechemobot_msgs.msg import RobotTask


class RobotTaskServer(Node):
    def __init__(self):
        super().__init__("robot_task_server")
        self.declare_parameter("task_duration_s", 2.0)
        self.declare_parameter("publish_rate_hz", 5.0)
        self.duration = float(self.get_parameter("task_duration_s").value)
        self.rate = float(self.get_parameter("publish_rate_hz").value)
        self.task_pub = self.create_publisher(RobotTask, "/robot/tasks", 10)
        self.group = ReentrantCallbackGroup()
        self.server = ActionServer(
            self,
            PickPlace,
            "/robot/pick_place",
            execute_callback=self.execute,
            goal_callback=lambda goal: GoalResponse.ACCEPT,
            cancel_callback=lambda goal: CancelResponse.ACCEPT,
            callback_group=self.group,
        )
        self.get_logger().info("Robot task server ready on /robot/pick_place")

    def publish_task(self, task_id, goal, state):
        msg = RobotTask()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "robot"
        msg.task_id = task_id
        msg.task_type = "pick_place"
        msg.robot_id = goal.robot_id or "amr_1"
        msg.source_location = goal.source_location
        msg.target_location = goal.target_location
        msg.container_id = goal.container_id
        msg.priority = 1.0
        msg.state = state
        self.task_pub.publish(msg)

    def execute(self, goal_handle):
        goal = goal_handle.request
        task_id = f"pick-{uuid.uuid4().hex[:8]}"
        started = time.monotonic()
        self.publish_task(task_id, goal, "accepted")
        self.get_logger().info(
            f"{task_id} {goal.container_id} {goal.source_location} -> {goal.target_location}")

        while time.monotonic() - started < self.duration:
            if goal_handle.is_cancel_requested:
                self.publish_task(task_id, goal, "canceled")
                goal_handle.canceled()
                result = PickPlace.Result()
                result.success = False
                result.message = "canceled"
                result.duration_s = time.monotonic() - started
                return result
            progress = min(1.0, (time.monotonic() - started) / max(0.1, self.duration))
            feedback = PickPlace.Feedback()
            feedback.stage = "transfer" if progress < 0.8 else "place"
            feedback.progress = progress
            goal_handle.publish_feedback(feedback)
            time.sleep(1.0 / self.rate)

        self.publish_task(task_id, goal, "complete")
        goal_handle.succeed()
        result = PickPlace.Result()
        result.success = True
        result.message = "pick and place complete"
        result.duration_s = time.monotonic() - started
        return result


def main(args=None):
    rclpy.init(args=args)
    node = RobotTaskServer()
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
