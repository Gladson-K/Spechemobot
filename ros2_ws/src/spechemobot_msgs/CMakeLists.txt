cmake_minimum_required(VERSION 3.16)
project(spechemobot_msgs)

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(std_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/ProcessState.msg"
  "msg/ThermalReading.msg"
  "msg/ContainerState.msg"
  "msg/RobotTask.msg"
  "msg/SafetyAlarm.msg"
  "msg/FurnaceCommand.msg"
  "action/PickPlace.action"
  "action/RunBatch.action"
  DEPENDENCIES std_msgs geometry_msgs builtin_interfaces
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()
