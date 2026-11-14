#include <algorithm>
#include <chrono>
#include <cmath>
#include <memory>
#include <string>
#include <vector>

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/opencv.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/image_encodings.hpp>
#include <sensor_msgs/msg/image.hpp>

#include "spechemobot_msgs/msg/thermal_reading.hpp"

#ifdef SPECHEMOBOT_HAS_ORT
#include <onnxruntime_cxx_api.h>
#endif

namespace spechemobot
{

class OnnxInferenceNode : public rclcpp::Node
{
public:
  OnnxInferenceNode()
  : Node("onnx_inference_node")
  {
    model_path_ = declare_parameter<std::string>("model_path", "");
    rgb_topic_ = declare_parameter<std::string>("rgb_topic", "/camera/image_raw");
    thermal_topic_ = declare_parameter<std::string>("thermal_topic", "/thermal_camera");
    output_topic_ = declare_parameter<std::string>("output_topic", "/perception/thermal_reading");
    inference_rate_ = declare_parameter<double>("inference_rate_hz", 10.0);
    max_thermal_c_ = declare_parameter<double>("max_thermal_c", 900.0);
    fallback_when_missing_ = declare_parameter<bool>("fallback_when_model_missing", true);

    publisher_ = create_publisher<spechemobot_msgs::msg::ThermalReading>(output_topic_, 10);
    rgb_subscription_ = create_subscription<sensor_msgs::msg::Image>(
      rgb_topic_, rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::Image::SharedPtr msg) { onRgb(msg); });
    thermal_subscription_ = create_subscription<sensor_msgs::msg::Image>(
      thermal_topic_, rclcpp::SensorDataQoS(),
      [this](sensor_msgs::msg::Image::SharedPtr msg) { onThermal(msg); });

    loadModel();

    const double period = inference_rate_ > 0.0 ? 1.0 / inference_rate_ : 0.1;
    timer_ = create_wall_timer(
      std::chrono::duration<double>(period),
      [this]() { infer(); });

    RCLCPP_INFO(
      get_logger(), "Perception ready rgb=%s thermal=%s output=%s model=%s",
      rgb_topic_.c_str(), thermal_topic_.c_str(), output_topic_.c_str(),
      model_loaded_ ? model_path_.c_str() : "fallback");
  }

private:
  void loadModel()
  {
    if (model_path_.empty()) {
      RCLCPP_WARN(get_logger(), "No model path configured; using thermal fallback");
      return;
    }

#ifdef SPECHEMOBOT_HAS_ORT
    try {
      env_ = std::make_unique<Ort::Env>(ORT_LOGGING_LEVEL_WARNING, "spechemobot_perception");
      session_options_.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
      session_ = std::make_unique<Ort::Session>(*env_, model_path_.c_str(), session_options_);

      Ort::AllocatorWithDefaultOptions allocator;
      for (size_t i = 0; i < session_->GetInputCount(); ++i) {
        auto name = session_->GetInputNameAllocated(i, allocator);
        input_names_.emplace_back(name.get());
      }
      for (size_t i = 0; i < session_->GetOutputCount(); ++i) {
        auto name = session_->GetOutputNameAllocated(i, allocator);
        output_names_.emplace_back(name.get());
      }
      model_loaded_ = true;
      RCLCPP_INFO(
        get_logger(), "Loaded ONNX model with %zu inputs and %zu outputs",
        input_names_.size(), output_names_.size());
    } catch (const std::exception & error) {
      RCLCPP_ERROR(get_logger(), "Failed to load ONNX model: %s", error.what());
      model_loaded_ = false;
    }
#else
    RCLCPP_WARN(get_logger(), "Built without ONNX Runtime; using thermal fallback");
#endif
  }

  void onRgb(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    try {
      rgb_ = cv_bridge::toCvCopy(msg)->image;
      rgb_stamp_ = rclcpp::Time(msg->header.stamp);
    } catch (const std::exception & error) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000, "RGB conversion failed: %s", error.what());
    }
  }

  void onThermal(const sensor_msgs::msg::Image::SharedPtr msg)
  {
    try {
      const cv::Mat raw = cv_bridge::toCvCopy(msg)->image;
      if (raw.depth() == CV_16U) {
        raw.convertTo(thermal_, CV_32F, 0.01, -273.15);
      } else if (raw.depth() == CV_32F) {
        raw.convertTo(thermal_, CV_32F);
        thermal_ -= 273.15f;
      } else if (raw.depth() == CV_8U) {
        cv::Mat gray;
        if (raw.channels() == 3) {
          cv::cvtColor(raw, gray, cv::COLOR_BGR2GRAY);
        } else {
          gray = raw;
        }
        gray.convertTo(thermal_, CV_32F, 1500.0 / 255.0, -50.0);
      } else {
        return;
      }
      thermal_stamp_ = rclcpp::Time(msg->header.stamp);
    } catch (const std::exception & error) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000, "Thermal conversion failed: %s", error.what());
    }
  }

  struct ThermalStats
  {
    double min_c = 0.0;
    double max_c = 0.0;
    double mean_c = 0.0;
    double hotspot_x = 0.5;
    double hotspot_y = 0.5;
    bool valid = false;
  };

  ThermalStats thermalStats() const
  {
    ThermalStats stats;
    if (thermal_.empty()) {
      return stats;
    }

    cv::Mat mask;
    cv::inRange(thermal_, -50.0, 5000.0, mask);
    if (cv::countNonZero(mask) == 0) {
      return stats;
    }

    double min_value = 0.0;
    double max_value = 0.0;
    cv::Point min_location;
    cv::Point max_location;
    cv::minMaxLoc(thermal_, &min_value, &max_value, &min_location, &max_location, mask);
    stats.min_c = min_value;
    stats.max_c = max_value;
    stats.mean_c = cv::mean(thermal_, mask)[0];
    stats.hotspot_x = (static_cast<double>(max_location.x) + 0.5) / static_cast<double>(thermal_.cols);
    stats.hotspot_y = (static_cast<double>(max_location.y) + 0.5) / static_cast<double>(thermal_.rows);
    stats.valid = std::isfinite(stats.mean_c);
    return stats;
  }

  std::vector<float> makeBlob(const cv::Mat & image, int channels, int height, int width, bool thermal) const
  {
    cv::Mat resized;
    cv::resize(image, resized, cv::Size(width, height));

    cv::Mat converted;
    if (channels == 3) {
      if (resized.channels() == 3) {
        cv::cvtColor(resized, converted, cv::COLOR_BGR2RGB);
      } else {
        cv::cvtColor(resized, converted, cv::COLOR_GRAY2RGB);
      }
    } else {
      if (resized.channels() == 3) {
        cv::cvtColor(resized, converted, cv::COLOR_BGR2GRAY);
      } else {
        converted = resized;
      }
    }

    cv::Mat float_image;
    converted.convertTo(float_image, CV_32F);
    if (thermal) {
      float_image = (float_image + 50.0f) / 1550.0f;
    } else {
      float_image /= 255.0f;
    }

    std::vector<float> blob(static_cast<size_t>(channels) * height * width, 0.0f);
    for (int y = 0; y < height; ++y) {
      for (int x = 0; x < width; ++x) {
        if (channels == 1) {
          blob[static_cast<size_t>(y) * width + x] = float_image.at<float>(y, x);
        } else {
          const cv::Vec3f pixel = float_image.at<cv::Vec3f>(y, x);
          for (int c = 0; c < 3; ++c) {
            blob[(static_cast<size_t>(c) * height + y) * width + x] = pixel[c];
          }
        }
      }
    }
    return blob;
  }

  bool runModel(const ThermalStats & stats, double & min_c, double & max_c, double & mean_c)
  {
#ifdef SPECHEMOBOT_HAS_ORT
    (void)stats;
    if (!model_loaded_ || input_names_.empty() || output_names_.empty()) {
      return false;
    }
    if (rgb_.empty() && thermal_.empty()) {
      return false;
    }

    try {
      std::vector<std::vector<float>> buffers;
      std::vector<std::vector<int64_t>> shapes;
      std::vector<Ort::Value> inputs;
      buffers.reserve(input_names_.size());
      shapes.reserve(input_names_.size());
      inputs.reserve(input_names_.size());

      for (size_t i = 0; i < input_names_.size(); ++i) {
        auto shape = session_->GetInputTypeInfo(i).GetTensorTypeAndShapeInfo().GetShape();
        if (shape.size() != 4) {
          return false;
        }
        shape[0] = 1;
        int channels = shape[1] > 0 ? static_cast<int>(shape[1]) : 3;
        int height = shape[2] > 0 ? static_cast<int>(shape[2]) : 224;
        int width = shape[3] > 0 ? static_cast<int>(shape[3]) : 224;
        shape[1] = channels;
        shape[2] = height;
        shape[3] = width;

        const bool use_thermal = thermal_.empty() ? false : (channels == 1 || i > 0);
        const cv::Mat & source = use_thermal ? thermal_ : rgb_;
        if (source.empty()) {
          return false;
        }
        buffers.push_back(makeBlob(source, channels, height, width, use_thermal));
        shapes.push_back(shape);
      }

      const Ort::MemoryInfo memory_info = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
      for (size_t i = 0; i < buffers.size(); ++i) {
        inputs.push_back(Ort::Value::CreateTensor<float>(
          memory_info, buffers[i].data(), buffers[i].size(), shapes[i].data(), shapes[i].size()));
      }

      std::vector<const char *> input_names;
      std::vector<const char *> output_names;
      for (const auto & name : input_names_) {
        input_names.push_back(name.c_str());
      }
      for (const auto & name : output_names_) {
        output_names.push_back(name.c_str());
      }

      auto outputs = session_->Run(
        Ort::RunOptions{nullptr}, input_names.data(), inputs.data(), inputs.size(),
        output_names.data(), output_names.size());

      if (outputs.empty()) {
        return false;
      }

      auto info = outputs[0].GetTensorTypeAndShapeInfo();
      if (info.GetElementType() != ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT || info.GetElementCount() < 3) {
        return false;
      }
      const float * values = outputs[0].GetTensorData<float>();
      const double model_min = values[0];
      const double model_max = values[1];
      const double model_mean = values[2];
      if (!std::isfinite(model_min) || !std::isfinite(model_max) || !std::isfinite(model_mean)) {
        return false;
      }
      if (model_max < model_min) {
        return false;
      }

      min_c = model_min;
      max_c = model_max;
      mean_c = model_mean;
      return true;
    } catch (const std::exception & error) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000, "ONNX inference failed: %s", error.what());
      return false;
    }
#else
    (void)stats;
    (void)min_c;
    (void)max_c;
    (void)mean_c;
    return false;
#endif
  }

  void infer()
  {
    const ThermalStats stats = thermalStats();
    if (!stats.valid && rgb_.empty()) {
      return;
    }

    double min_c = stats.min_c;
    double max_c = stats.max_c;
    double mean_c = stats.mean_c;
    const bool model_used = runModel(stats, min_c, max_c, mean_c) || !fallback_when_missing_;

    if (!stats.valid && !model_used) {
      return;
    }

    spechemobot_msgs::msg::ThermalReading reading;
    if (thermal_stamp_.nanoseconds() > 0) {
      reading.header.stamp = thermal_stamp_;
    } else if (rgb_stamp_.nanoseconds() > 0) {
      reading.header.stamp = rgb_stamp_;
    } else {
      reading.header.stamp = now();
    }
    reading.header.frame_id = "thermal_camera";
    reading.sensor_id = model_used ? "onnx-thermal" : "thermal-fallback";
    reading.min_temperature_c = static_cast<float>(min_c);
    reading.max_temperature_c = static_cast<float>(max_c);
    reading.mean_temperature_c = static_cast<float>(mean_c);
    reading.hotspot_x = static_cast<float>(stats.hotspot_x);
    reading.hotspot_y = static_cast<float>(stats.hotspot_y);
    reading.over_temperature = max_c > max_thermal_c_;
    publisher_->publish(reading);
  }

  std::string model_path_;
  std::string rgb_topic_;
  std::string thermal_topic_;
  std::string output_topic_;
  double inference_rate_ = 10.0;
  double max_thermal_c_ = 900.0;
  bool fallback_when_missing_ = true;
  bool model_loaded_ = false;

  cv::Mat rgb_;
  cv::Mat thermal_;
  rclcpp::Time rgb_stamp_{0, 0, RCL_ROS_TIME};
  rclcpp::Time thermal_stamp_{0, 0, RCL_ROS_TIME};

  rclcpp::Publisher<spechemobot_msgs::msg::ThermalReading>::SharedPtr publisher_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr rgb_subscription_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr thermal_subscription_;
  rclcpp::TimerBase::SharedPtr timer_;

#ifdef SPECHEMOBOT_HAS_ORT
  std::unique_ptr<Ort::Env> env_;
  Ort::SessionOptions session_options_;
  std::unique_ptr<Ort::Session> session_;
#endif
  std::vector<std::string> input_names_;
  std::vector<std::string> output_names_;
};

}  // namespace spechemobot

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<spechemobot::OnnxInferenceNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
