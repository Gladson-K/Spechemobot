require "securerandom"
require "spechemobot/ros2_cli"

module Spechemobot
  class Orchestrator
    REQUIRED_NODES = %w[
      /batch_orchestrator
      /tep_replay_node
      /robot_task_server
      /safety_monitor_node
    ].freeze

    attr_reader :ros2, :defaults

    def initialize(ros2:, defaults: {})
      @ros2 = ros2
      @defaults = defaults
    end

    def health
      nodes = ros2.node_list
      {
        ok: (REQUIRED_NODES - nodes).empty?,
        required_nodes: REQUIRED_NODES,
        missing_nodes: REQUIRED_NODES - nodes,
        nodes: nodes
      }
    end

    def state(topic = "/process/state")
      ros2.topic_once(topic)
    end

    def submit_batch(target_temperature_c: nil, hold_time_s: nil, product_id: nil, batch_id: nil)
      ros2.send_batch_goal(
        target_temperature_c: target_temperature_c || defaults.fetch("target_temperature_c", 450.0),
        hold_time_s: hold_time_s || defaults.fetch("hold_time_s", 8.0),
        product_id: product_id || defaults.fetch("product_id", "P-100"),
        batch_id: batch_id.to_s.empty? ? "batch-#{SecureRandom.hex(4)}" : batch_id,
        feedback: true
      )
    end

    def pick(container_id:, robot_id: "amr_1", source_location: "conveyor",
             target_location: "packaging", approach_height_m: 0.25)
      ros2.send_pick_goal(
        container_id: container_id,
        robot_id: robot_id,
        source_location: source_location,
        target_location: target_location,
        approach_height_m: approach_height_m
      )
    end

    def estop(engage = true)
      ros2.engage_estop(engage)
    end

    def reset
      ros2.reset_safety
    end
  end
end
