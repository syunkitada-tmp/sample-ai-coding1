Feature: Slack Proxy Debug Server
  In order to verify command execution results without a real Slack proxy
  As a developer
  I want a debug stub server that prints received payloads to stdout and returns ok

  Scenario: POST /post prints the payload to stdout and returns ok
    Given the debug proxy server is running
    When a POST request is sent to "/post" with JSON body containing channel "C12345678", text "Hello, world!", and thread_ts "1234567890.000000"
    Then the response status is 200
    And the response body is {"ok": true}
    And the payload is printed to stdout

  Scenario: POST /post without thread_ts also succeeds
    Given the debug proxy server is running
    When a POST request is sent to "/post" with JSON body containing channel "C12345678" and text "Hello, world!" without thread_ts
    Then the response status is 200
    And the response body is {"ok": true}
    And the payload is printed to stdout
