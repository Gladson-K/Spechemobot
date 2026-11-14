from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    share = get_package_share_directory("spechemobot_process")
    config = os.path.join(share, "config", "process.yaml")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("config", default_value=config),
        Node(
            package="spechemobot_process",
            executable="tep_replay_node",
            name="tep_replay_node",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
        Node(
            package="spechemobot_process",
            executable="furnace_model_node",
            name="furnace_model_node",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
        Node(
            package="spechemobot_process",
            executable="safety_monitor_node",
            name="safety_monitor_node",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
        Node(
            package="spechemobot_process",
            executable="container_manager_node",
            name="container_manager_node",
            parameters=[LaunchConfiguration("config"), {"use_sim_time": use_sim_time}],
            output="screen",
        ),
    ])
