Feature: Persist Message and Enqueue Command Job
  In order to process commands reliably
  As the ChatOps framework
  I want to persist every received message and atomically register a job when a command is detected

  Scenario: Persist a plain message without a command
    Given the message reception API is running
    And the "chatops-alert" shell command is available
    When a POST request is received with text "Good morning"
    Then the message is saved to the database
    And no job record is created

  Scenario: Persist a message and enqueue a job for a valid command
    Given the message reception API is running
    And the "chatops-alert" shell command is available
    When a POST request is received with text "!alert --host web01"
    Then the message is saved to the database
    And a job record is created with command "alert", args "--host web01", and status "pending"
    And the job record contains the Slack thread context

  Scenario: Reject a message containing multiple commands
    Given the message reception API is running
    And the "chatops-alert" shell command is available
    When a POST request is received with text "!alert --host web01\n!help"
    Then the message is saved to the database
    And no job record is created
    And an error notification is posted to the Slack thread

  Scenario: Reject a message with an unknown command
    Given the message reception API is running
    And no shell command named "chatops-unknown" is registered
    When a POST request is received with text "!unknown --foo bar"
    Then the message is saved to the database
    And no job record is created
    And an error notification is posted to the Slack thread

  Scenario: Message save and job registration succeed or fail atomically
    Given the message reception API is running
    And the "chatops-alert" shell command is available
    When a POST request is received with text "!alert --host web01"
    And the database write fails mid-transaction
    Then neither the message nor the job record is persisted

  Scenario: trace_id is stored in the job record when a command is enqueued
    Given the message reception API is running
    And the "chatops-alert" shell command is available
    When a POST request is received with text "!alert --host web01"
    Then the message is saved to the database
    And a job record is created with command "alert"
    And the job record contains the trace_id used for the current request
