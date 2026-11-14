require "minitest/autorun"

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))

require "json"
require "spechemobot/ros2_cli"

class Ros2CliTest < Minitest::Test
  Result = Spechemobot::Ros2Cli::CommandResult

  def test_send_batch_goal_builds_ros2_action_command
    captured = nil
    runner = lambda do |args|
      captured = args
      Result.new(stdout: "success: true\nmessage: accepted\n", stderr: "", success: true, exitstatus: 0)
    end

    cli = Spechemobot::Ros2Cli.new(runner: runner)
    result = cli.send_batch_goal(
      target_temperature_c: 425.0,
      hold_time_s: 4.0,
      product_id: "P-200",
      batch_id: "batch-test"
    )

    assert result[:success]
    assert_equal "accepted", result[:message]
    assert_equal "action", captured[0]
    assert_equal "send_goal", captured[1]
    assert_equal "/process/run_batch", captured[2]
    assert_equal "spechemobot_msgs/action/RunBatch", captured[3]
    assert_equal(
      {
        "batch_id" => "batch-test",
        "target_temperature_c" => 425.0,
        "hold_time_s" => 4.0,
        "product_id" => "P-200"
      },
      JSON.parse(captured[4])
    )
    assert_includes captured, "--feedback"
  end

  def test_send_pick_goal_builds_ros2_action_command
    captured = nil
    runner = lambda do |args|
      captured = args
      Result.new(stdout: "success: false\nmessage: canceled\n", stderr: "", success: true, exitstatus: 0)
    end

    cli = Spechemobot::Ros2Cli.new(runner: runner)
    result = cli.send_pick_goal(container_id: "C-002", target_location: "storage")

    refute result[:success]
    assert_equal "canceled", result[:message]
    assert_equal "/robot/pick_place", captured[2]
    assert_equal "storage", JSON.parse(captured[4])["target_location"]
  end

  def test_topic_once_parses_yaml
    runner = lambda do |_args|
      Result.new(stdout: "---\nphase: holding\ntemperature: 451.5\n", stderr: "", success: true, exitstatus: 0)
    end

    cli = Spechemobot::Ros2Cli.new(runner: runner)
    assert_equal({ "phase" => "holding", "temperature" => 451.5 }, cli.topic_once("/process/state"))
  end

  def test_unavailable_ros2_raises
    runner = ->(_args) { raise Errno::ENOENT }

    cli = Spechemobot::Ros2Cli.new(runner: runner)
    assert_raises(Spechemobot::Ros2Cli::Unavailable) { cli.node_list }
  end
end
