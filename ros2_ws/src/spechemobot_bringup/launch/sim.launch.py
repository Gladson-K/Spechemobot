import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def bool_value(value):
    return value.strip().lower() in ("1", "true", "yes", "on")


def launch_setup(context, *args, **kwargs):
    sim_backend = LaunchConfiguration("sim_backend").perform(context)
    world = LaunchConfiguration("world").perform(context)
    world_file = LaunchConfiguration("world_file").perform(context)
    sim_root = Path(LaunchConfiguration("sim_root").perform(context)).resolve()
    headless = bool_value(LaunchConfiguration("headless").perform(context))
    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)
    launch_process = bool_value(LaunchConfiguration("launch_process").perform(context))
    launch_perception = bool_value(LaunchConfiguration("launch_perception").perform(context))
    launch_robot_state = bool_value(LaunchConfiguration("launch_robot_state").perform(context))
    launch_orchestration = bool_value(LaunchConfiguration("launch_orchestration").perform(context))
    launch_recording = bool_value(LaunchConfiguration("launch_recording").perform(context))
    launch_eval = bool_value(LaunchConfiguration("launch_eval").perform(context))
    session_name = LaunchConfiguration("session_name").perform(context)
    eval_duration = LaunchConfiguration("eval_duration_s").perform(context)
    verbose = LaunchConfiguration("verbose").perform(context)
    bridge_config = LaunchConfiguration("bridge_config").perform(context)
    model_path = LaunchConfiguration("model_path").perform(context)
    o3de_executable = Path(LaunchConfiguration("o3de_executable").perform(context)).resolve()
    o3de_project = Path(LaunchConfiguration("o3de_project").perform(context)).resolve()
    o3de_rhi = LaunchConfiguration("o3de_rhi").perform(context)

    if not world_file:
        world_file = str(sim_root / "sim" / "gazebo" / "worlds" / f"{world}.sdf")
    world_path = Path(world_file).resolve()

    actions = []

    models_dir = sim_root / "sim" / "gazebo" / "models"
    resource_paths = [
        value
        for value in [
            os.environ.get("GZ_SIM_RESOURCE_PATH", ""),
            str(models_dir),
            str(world_path.parent),
        ]
        if value
    ]
    actions.append(SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", os.pathsep.join(resource_paths)))

    if sim_backend == "gazebo":
        if not world_path.is_file():
            raise RuntimeError(f"Gazebo world not found: {world_path}")
        gz_args = f"-r -v {verbose}"
        if headless:
            gz_args += " -s"
        gz_args += f" {world_path}"

        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
                ),
                launch_arguments={"gz_args": gz_args}.items(),
            )
        )
        actions.append(
            Node(
                package="ros_gz_bridge",
                executable="parameter_bridge",
                name="gz_bridge",
                parameters=[{"config_file": bridge_config, "use_sim_time": use_sim_time}],
                output="screen",
            )
        )
    elif sim_backend == "o3de":
        if headless:
            o3de_rhi = "null"
        if o3de_executable.is_file():
            command = [
                str(o3de_executable),
                f"-rhi={o3de_rhi}",
                f"--project-path={o3de_project}",
            ]
            actions.append(ExecuteProcess(cmd=command, output="screen"))
        else:
            actions.append(
                LogInfo(
                    msg=(
                        f"O3DE launcher not found: {o3de_executable}. "
                        "Build the project with: cmake --build build/linux --target SpechemobotO3DE.GameLauncher"
                    )
                )
            )
    else:
        raise RuntimeError(f"Unsupported SIM_BACKEND: {sim_backend}")

    if launch_robot_state:
        description_share = get_package_share_directory("spechemobot_description")
        xacro_file = os.path.join(description_share, "urdf", "spechemobot_cell.urdf.xacro")
        robot_description = ParameterValue(Command(["xacro ", xacro_file]), value_type=str)
        actions.append(
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                name="robot_state_publisher",
                parameters=[{"robot_description": robot_description, "use_sim_time": use_sim_time}],
                output="screen",
            )
        )
        actions.append(
            Node(
                package="joint_state_publisher",
                executable="joint_state_publisher",
                name="joint_state_publisher",
                parameters=[{"use_sim_time": use_sim_time}],
                output="screen",
            )
        )

    if launch_process:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("spechemobot_process"), "launch", "process.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            )
        )

    if launch_perception:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("spechemobot_perception"), "launch", "perception.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time, "model_path": model_path}.items(),
            )
        )

    if launch_orchestration:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("spechemobot_orchestration"), "launch", "orchestration.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time}.items(),
            )
        )

    if launch_recording:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("spechemobot_dataset"), "launch", "record.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time, "session_name": session_name}.items(),
            )
        )

    if launch_eval:
        actions.append(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(get_package_share_directory("spechemobot_eval"), "launch", "eval.launch.py")
                ),
                launch_arguments={"use_sim_time": use_sim_time, "duration_s": eval_duration}.items(),
            )
        )

    return actions


def generate_launch_description():
    default_root = os.environ.get("SIM_ROOT", "/workspace/Spechemobot")
    default_model = os.environ.get(
        "SPECHEMOBOT_THERMAL_MODEL",
        str(Path(default_root) / "models" / "spechemobot_thermal.onnx"),
    )

    return LaunchDescription([
        DeclareLaunchArgument("sim_backend", default_value=os.environ.get("SIM_BACKEND", "gazebo")),
        DeclareLaunchArgument("world", default_value=os.environ.get("SIM_WORLD", "reactor_hall")),
        DeclareLaunchArgument("world_file", default_value=""),
        DeclareLaunchArgument("sim_root", default_value=default_root),
        DeclareLaunchArgument("headless", default_value=os.environ.get("HEADLESS", "false")),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("launch_process", default_value="true"),
        DeclareLaunchArgument("launch_perception", default_value="true"),
        DeclareLaunchArgument("launch_robot_state", default_value="true"),
        DeclareLaunchArgument("launch_orchestration", default_value="true"),
        DeclareLaunchArgument("launch_recording", default_value="false"),
        DeclareLaunchArgument("launch_eval", default_value="false"),
        DeclareLaunchArgument("session_name", default_value=""),
        DeclareLaunchArgument("eval_duration_s", default_value="60.0"),
        DeclareLaunchArgument("verbose", default_value="4"),
        DeclareLaunchArgument(
            "bridge_config",
            default_value=os.path.join(get_package_share_directory("spechemobot_bringup"), "config", "gz_bridge.yaml"),
        ),
        DeclareLaunchArgument("model_path", default_value=default_model),
        DeclareLaunchArgument(
            "o3de_executable",
            default_value=str(
                Path(default_root) / "sim" / "o3de" / "SpechemobotO3DE" / "build" / "linux" / "bin" / "profile"
                / "SpechemobotO3DE.GameLauncher"
            ),
        ),
        DeclareLaunchArgument(
            "o3de_project",
            default_value=str(Path(default_root) / "sim" / "o3de" / "SpechemobotO3DE"),
        ),
        DeclareLaunchArgument("o3de_rhi", default_value=os.environ.get("O3DE_RHI", "vulkan")),
        OpaqueFunction(function=launch_setup),
    ])
