cmake_minimum_required(VERSION 3.16)
project(spechemobot_perception)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)
find_package(spechemobot_msgs REQUIRED)

set(ONNXRUNTIME_ROOT "$ENV{ONNXRUNTIME_ROOT}")
if(NOT ONNXRUNTIME_ROOT)
  set(ONNXRUNTIME_ROOT "/opt/onnxruntime")
endif()

find_path(ONNXRUNTIME_INCLUDE_DIR onnxruntime_cxx_api.h
  PATHS "${ONNXRUNTIME_ROOT}" "${ONNXRUNTIME_ROOT}/include"
)
find_library(ONNXRUNTIME_LIBRARY onnxruntime
  PATHS "${ONNXRUNTIME_ROOT}/lib" "${ONNXRUNTIME_ROOT}/lib64"
)

add_executable(onnx_inference_node src/onnx_inference_node.cpp)

ament_target_dependencies(onnx_inference_node
  rclcpp
  sensor_msgs
  std_msgs
  cv_bridge
  spechemobot_msgs
)

target_include_directories(onnx_inference_node PRIVATE ${OpenCV_INCLUDE_DIRS})
target_link_libraries(onnx_inference_node cv_bridge::cv_bridge ${OpenCV_LIBS})

if(ONNXRUNTIME_INCLUDE_DIR AND ONNXRUNTIME_LIBRARY)
  target_include_directories(onnx_inference_node PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
  target_link_libraries(onnx_inference_node ${ONNXRUNTIME_LIBRARY})
  target_compile_definitions(onnx_inference_node PRIVATE SPECHEMOBOT_HAS_ORT=1)
  message(STATUS "ONNX Runtime enabled: ${ONNXRUNTIME_LIBRARY}")
else()
  message(WARNING "ONNX Runtime not found; building thermal fallback only")
endif()

install(TARGETS onnx_inference_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

ament_package()
