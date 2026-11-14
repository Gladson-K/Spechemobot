from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(get_package_share_directory("spechemobot_orchestration"), "config", "orchestration.yaml")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("config", default_value=config),
        Node(
            package="spechemobot_orchestration",
            executable="robot_task_server",
            name="robot_task_server",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
        Node(
            package="spechemobot_orchestration",
            executable="batch_orchestrator",
            name="batch_orchestrator",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
    ])
