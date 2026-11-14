import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    sim_launch = os.path.join(get_package_share_directory("spechemobot_bringup"), "launch", "sim.launch.py")
    return LaunchDescription([
        DeclareLaunchArgument("sim_backend", default_value=os.environ.get("SIM_BACKEND", "gazebo")),
        DeclareLaunchArgument("headless", default_value=os.environ.get("HEADLESS", "false")),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(sim_launch),
            launch_arguments={
                "world": "sensor_qualification",
                "sim_backend": LaunchConfiguration("sim_backend"),
                "headless": LaunchConfiguration("headless"),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }.items(),
        ),
    ])
