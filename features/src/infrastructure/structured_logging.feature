Feature: Structured Logging with Source Location and Trace ID
  In order to investigate incidents and trace request flows efficiently
  As a system operator
  I want all log entries to include source file location and a trace_id that spans the entire job lifecycle

  Scenario: Log entries include source file name and line number
    Given the logging system is configured
    When any log message is emitted
    Then the log entry includes the source file name
    And the log entry includes the line number

  Scenario: API request generates a unique trace ID
    Given the message reception API is running
    When a POST request is received
    Then a new UUID trace_id is generated for the request
    And all log entries during the request include the trace_id

  Scenario: trace_id is stored in the job record when a command is enqueued
    Given the message reception API is running
    And the plugin "alert" is registered
    When a POST request is received with text "!alert --host web01"
    Then the created job record contains the trace_id from the request

  Scenario: Worker restores trace_id from job record to logging context
    Given the worker is running
    And a job with trace_id "abc-123" exists in the database
    When the worker picks up the job
    Then the logging context contains trace_id "abc-123"
    And all log entries during job execution include trace_id "abc-123"

  Scenario: Logs without an active trace_id use a placeholder
    Given the logging system is configured
    When a log message is emitted outside of any request or job context
    Then the log entry contains trace_id "-"
