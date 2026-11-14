from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    default_model = os.environ.get("SPECHEMOBOT_THERMAL_MODEL", "/workspace/Spechemobot/models/spechemobot_thermal.onnx")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("model_path", default_value=default_model),
        DeclareLaunchArgument("rgb_topic", default_value="/camera/image_raw"),
        DeclareLaunchArgument("thermal_topic", default_value="/thermal_camera"),
        DeclareLaunchArgument("output_topic", default_value="/perception/thermal_reading"),
        Node(
            package="spechemobot_perception",
            executable="onnx_inference_node",
            name="onnx_inference_node",
            parameters=[{
                "use_sim_time": use_sim_time,
                "model_path": LaunchConfiguration("model_path"),
                "rgb_topic": LaunchConfiguration("rgb_topic"),
                "thermal_topic": LaunchConfiguration("thermal_topic"),
                "output_topic": LaunchConfiguration("output_topic"),
                "inference_rate_hz": 10.0,
                "max_thermal_c": 900.0,
                "fallback_when_model_missing": True,
            }],
            output="screen",
        ),
    ])
