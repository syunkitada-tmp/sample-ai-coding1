Feature: Dummy Alert Command
  In order to provide a reference implementation for plugin development
  As a developer
  I want the built-in "!alert" dummy command to echo received arguments and thread context back to Slack

  Scenario: Successfully execute !alert with required --host option
    Given the "alert" plugin is registered
    And a job with command "alert", args "--host web01", and valid thread context exists
    When the worker executes the job
    Then the job status changes to "done"
    And the Slack thread receives a reply containing "--host web01" and the thread context

  Scenario: Execute !alert with --host option and positional arguments
    Given the "alert" plugin is registered
    And a job with command "alert" and args "--host web01 app01" exists
    When the worker executes the job
    Then the Slack thread receives a reply containing "--host web01" and "app01"

  Scenario: Fail when --host option is missing
    Given the "alert" plugin is registered
    And a job with command "alert" and args "app01" exists with no --host option
    When the worker executes the job
    Then the job status changes to "failed" without retry
    And the Slack thread receives an error reply stating "--host is required"
