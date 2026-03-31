Feature: Receive Message
  In order to process operator commands from Slack
  As the ChatOps framework
  I want to accept incoming messages via an HTTP endpoint

  Scenario: Successfully receive a message with all required fields
    Given the message reception API is running
    When a POST request is received with channel_id "C123", thread_ts "1234567890.000100", user "U456", text "Hello", and timestamp "1234567890.000100"
    Then the API returns HTTP 200

  Scenario Outline: Reject a request with a missing required field
    Given the message reception API is running
    When a POST request is received with the "<field>" field missing
    Then the API returns HTTP 400

    Examples:
      | field      |
      | channel_id |
      | user       |
      | text       |
      | timestamp  |

  Scenario: Reject a request with an empty body
    Given the message reception API is running
    When a POST request is received with an empty body
    Then the API returns HTTP 400
