from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(get_package_share_directory("spechemobot_eval"), "config", "eval.yaml")
    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("config", default_value=config),
        DeclareLaunchArgument("duration_s", default_value="60.0"),
        Node(
            package="spechemobot_eval",
            executable="evaluate_run",
            name="evaluate_run",
            parameters=[
                LaunchConfiguration("config"),
                {
                    "use_sim_time": LaunchConfiguration("use_sim_time"),
                    "duration_s": LaunchConfiguration("duration_s"),
                },
            ],
            output="screen",
        ),
    ])
