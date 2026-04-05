Feature: Dummy Alert Command
  In order to provide a reference implementation for shell-based command development
  As a developer
  I want the built-in "!alert" dummy command (chatops-alert) to echo received arguments back to Slack as JSON or text output

  Scenario: Successfully execute !alert with required --host option
    Given the "chatops-alert" shell command is executable
    And a job with command "alert", args "--host web01", and valid thread context exists
    When the worker executes the job via subprocess
    Then the job status changes to "done"
    And the stdout output is parsed (JSON or plain text)
    And the Slack thread receives a reply containing the parsed result

  Scenario: Execute !alert with --host option and positional arguments
    Given the "chatops-alert" shell command is executable
    And a job with command "alert" and args "--host web01 app01" exists
    When the worker executes the job via subprocess
    Then the Slack thread receives a reply containing the parsed output

  Scenario: Fail when --host option is missing
    Given the "chatops-alert" shell command is executable
    And a job with command "alert" and args "app01" exists with no --host option
    When the worker executes the job
    And the subprocess exits with a non-zero exit code
    Then the job is marked as "failed" (user error, no retry)
    And the error message from the JSON output is posted to Slack
