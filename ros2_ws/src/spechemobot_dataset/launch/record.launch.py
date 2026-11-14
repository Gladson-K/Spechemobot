from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(get_package_share_directory("spechemobot_dataset"), "config", "dataset.yaml")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("config", default_value=config),
        DeclareLaunchArgument("session_name", default_value=""),
        DeclareLaunchArgument("output_dir", default_value="/workspace/Spechemobot/datasets/raw"),
        Node(
            package="spechemobot_dataset",
            executable="record_dataset",
            name="record_dataset",
            parameters=[
                LaunchConfiguration("config"),
                {
                    "use_sim_time": use_sim_time,
                    "session_name": LaunchConfiguration("session_name"),
                    "output_dir": LaunchConfiguration("output_dir"),
                },
            ],
            output="screen",
        ),
    ])
