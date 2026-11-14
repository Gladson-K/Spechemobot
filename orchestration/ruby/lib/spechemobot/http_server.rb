require "json"
require "socket"

module Spechemobot
  class HttpServer
    STATUS_TEXT = {
      200 => "OK",
      400 => "Bad Request",
      404 => "Not Found",
      405 => "Method Not Allowed",
      500 => "Internal Server Error"
    }.freeze

    def initialize(host:, port:, orchestrator:, logger: $stdout)
      @host = host
      @port = port
      @orchestrator = orchestrator
      @logger = logger
    end

    def start
      server = TCPServer.new(@host, @port)
      @logger.puts("spechemobot-ruby listening on http://#{@host}:#{@port}")
      loop do
        socket = server.accept
        Thread.new(socket) { |client| handle(client) }
      end
    ensure
      server&.close
    end

    def route(method, path, payload)
      case [method, path]
      when ["GET", "/health"]
        [200, @orchestrator.health]
      when ["GET", "/state"]
        [200, @orchestrator.state]
      when ["POST", "/batch"]
        [200, @orchestrator.submit_batch(
          target_temperature_c: payload["target_temperature_c"],
          hold_time_s: payload["hold_time_s"],
          product_id: payload["product_id"],
          batch_id: payload["batch_id"]
        )]
      when ["POST", "/pick"]
        [200, @orchestrator.pick(
          container_id: payload.fetch("container_id"),
          robot_id: payload.fetch("robot_id", "amr_1"),
          source_location: payload.fetch("source_location", "conveyor"),
          target_location: payload.fetch("target_location", "packaging"),
          approach_height_m: payload.fetch("approach_height_m", 0.25)
        )]
      when ["POST", "/estop"]
        [200, @orchestrator.estop(payload.fetch("engage", true))]
      when ["POST", "/reset"]
        [200, @orchestrator.reset]
      else
        known_path = %w[/health /state /batch /pick /estop /reset].include?(path)
        [known_path ? 405 : 404, { error: known_path ? "method not allowed" : "not found" }]
      end
    rescue KeyError => error
      [400, { error: error.message }]
    rescue StandardError => error
      [500, { error: error.class.name, message: error.message }]
    end

    private

    def handle(socket)
      request_line = socket.gets
      return unless request_line

      method, path, = request_line.split
      headers = read_headers(socket)
      body = read_body(socket, headers)
      payload = body.empty? ? {} : JSON.parse(body)
      status, response = route(method, path, payload)
      write_response(socket, status, response)
    rescue JSON::ParserError
      write_response(socket, 400, { error: "invalid JSON body" })
    rescue StandardError => error
      write_response(socket, 500, { error: error.class.name, message: error.message })
    ensure
      socket.close
    end

    def read_headers(socket)
      headers = {}
      while (line = socket.gets)
        break if line == "\r\n" || line == "\n"

        key, value = line.split(":", 2)
        headers[key.downcase] = value.strip if key && value
      end
      headers
    end

    def read_body(socket, headers)
      length = headers.fetch("content-length", "0").to_i
      length.positive? ? socket.read(length).to_s : ""
    end

    def write_response(socket, status, payload)
      body = JSON.generate(payload)
      socket.write("HTTP/1.1 #{status} #{STATUS_TEXT.fetch(status, 'Unknown')}\r\n")
      socket.write("Content-Type: application/json\r\n")
      socket.write("Content-Length: #{body.bytesize}\r\n")
      socket.write("Connection: close\r\n\r\n")
      socket.write(body)
    end
  end
end
