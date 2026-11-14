require "minitest/autorun"

$LOAD_PATH.unshift(File.expand_path("../lib", __dir__))

require "spechemobot/orchestrator"

class OrchestratorTest < Minitest::Test
  class FakeRos2
    attr_reader :batch_goal, :pick_goal, :estop_value

    def node_list
      Spechemobot::Orchestrator::REQUIRED_NODES
    end

    def topic_once(_topic)
      { "phase" => "idle" }
    end

    def send_batch_goal(**goal)
      @batch_goal = goal
      { success: true, message: "ok", output: "" }
    end

    def send_pick_goal(**goal)
      @pick_goal = goal
      { success: true, message: "ok", output: "" }
    end

    def engage_estop(value)
      @estop_value = value
      { success: true }
    end

    def reset_safety
      { success: true }
    end
  end

  def setup
    @ros2 = FakeRos2.new
    @orchestrator = Spechemobot::Orchestrator.new(
      ros2: @ros2,
      defaults: { "target_temperature_c" => 400.0, "hold_time_s" => 2.0, "product_id" => "P-1" }
    )
  end

  def test_health_ok
    assert @orchestrator.health[:ok]
    assert_empty @orchestrator.health[:missing_nodes]
  end

  def test_submit_batch_applies_defaults_and_generates_id
    result = @orchestrator.submit_batch
    assert result[:success]
    assert_equal 400.0, @ros2.batch_goal[:target_temperature_c]
    assert_equal 2.0, @ros2.batch_goal[:hold_time_s]
    assert_equal "P-1", @ros2.batch_goal[:product_id]
    assert_match(/\Abatch-[0-9a-f]{8}\z/, @ros2.batch_goal[:batch_id])
  end

  def test_pick_passes_explicit_goal
    @orchestrator.pick(container_id: "C-004", target_location: "storage")
    assert_equal "C-004", @ros2.pick_goal[:container_id]
    assert_equal "storage", @ros2.pick_goal[:target_location]
  end

  def test_estop_engages
    @orchestrator.estop
    assert_equal true, @ros2.estop_value
  end
end
