require "json"
require "open3"
require "timeout"
require "yaml"

module Spechemobot
  class Ros2Cli
    class Unavailable < StandardError; end
    class TimeoutError < StandardError; end

    CommandResult = Struct.new(:stdout, :stderr, :success, :exitstatus, keyword_init: true)

    attr_reader :timeout_s

    def initialize(timeout_s: 30, env: {}, runner: nil)
      @timeout_s = timeout_s
      @env = env
      @runner = runner || method(:capture)
    end

    def send_batch_goal(target_temperature_c:, hold_time_s:, product_id:, batch_id: nil, feedback: true)
      goal = {
        batch_id: batch_id.to_s,
        target_temperature_c: Float(target_temperature_c),
        hold_time_s: Float(hold_time_s),
        product_id: product_id.to_s
      }
      result = run(
        "action", "send_goal", "/process/run_batch",
        "spechemobot_msgs/action/RunBatch",
        JSON.generate(goal),
        *(feedback ? ["--feedback"] : [])
      )
      parse_action_result(result)
    end

    def send_pick_goal(container_id:, robot_id: "amr_1", source_location: "conveyor",
                       target_location: "packaging", approach_height_m: 0.25)
      goal = {
        container_id: container_id.to_s,
        robot_id: robot_id.to_s,
        source_location: source_location.to_s,
        target_location: target_location.to_s,
        approach_height_m: Float(approach_height_m)
      }
      result = run(
        "action", "send_goal", "/robot/pick_place",
        "spechemobot_msgs/action/PickPlace",
        JSON.generate(goal),
        "--feedback"
      )
      parse_action_result(result)
    end

    def topic_once(topic)
      result = expect_success(run("topic", "echo", "--once", topic))
      parse_yaml(result.stdout)
    end

    def publish_once(topic, type, value)
      result = run("topic", "pub", "--once", topic, type, JSON.generate(value))
      expect_success(result)
      { success: true, output: result.stdout.strip }
    end

    def call_service(service, type, value = {})
      result = run("service", "call", service, type, JSON.generate(value))
      expect_success(result)
      { success: true, output: result.stdout.strip }
    end

    def engage_estop(engage = true)
      publish_once("/safety/estop", "std_msgs/msg/Bool", { data: !!engage })
    end

    def reset_safety
      call_service("/safety/reset", "std_srvs/srv/Trigger")
    end

    def node_list
      result = expect_success(run("node", "list"))
      result.stdout.lines.map(&:strip).reject(&:empty?)
    end

    def parse_action_result(result)
      text = [result.stdout, result.stderr].reject { |value| value.nil? || value.empty? }.join("\n")
      success = if (match = text.match(/^\s*success:\s*(true|false)\s*$/i))
                  match[1].casecmp("true").zero?
                else
                  result.success
                end
      message = text[/^\s*message:\s*(.+)$/i, 1]&.strip
      {
        success: success,
        message: message,
        output: text.strip
      }
    end

    private

    def capture(args)
      stdout, stderr, status = Timeout.timeout(@timeout_s) do
        Open3.capture3(@env, "ros2", *args)
      end
      CommandResult.new(
        stdout: stdout,
        stderr: stderr,
        success: status.success?,
        exitstatus: status.exitstatus
      )
    rescue Errno::ENOENT
      raise Unavailable, "ros2 command not found; source /opt/ros/<distro>/setup.bash"
    rescue Timeout::Error
      raise TimeoutError, "ros2 command timed out after #{@timeout_s}s: ros2 #{args.join(' ')}"
    end

    def run(*args)
      @runner.call(args.map(&:to_s))
    rescue Errno::ENOENT
      raise Unavailable, "ros2 command not found; source /opt/ros/<distro>/setup.bash"
    rescue Timeout::Error
      raise TimeoutError, "ros2 command timed out after #{@timeout_s}s: ros2 #{args.join(' ')}"
    end

    def expect_success(result)
      return result if result.success

      detail = [result.stderr, result.stdout].reject { |value| value.nil? || value.empty? }.join("\n").strip
      raise Unavailable, detail.empty? ? "ros2 command failed" : detail
    end

    def parse_yaml(text)
      cleaned = text.sub(/\A---\s*\n?/, "").sub(/\.\.\.\s*\z/, "").strip
      YAML.safe_load(cleaned, permitted_classes: [Time], aliases: false) || {}
    rescue Psych::Exception
      { "raw" => text.strip }
    end
  end
end
