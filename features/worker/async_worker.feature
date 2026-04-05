Feature: Async Command Worker
  In order to execute commands without blocking the message reception API
  As the ChatOps framework
  I want a worker process to poll the database and execute pending jobs concurrently via subprocess

  Scenario: Worker picks up a pending job and executes it successfully
    Given the worker is running
    And a job with status "pending" and command "alert" exists in the database
    And the "chatops-alert" shell command is executable
    When the worker polls the database
    Then the job status changes to "processing"
    And the worker executes "chatops-alert" via subprocess with command line arguments
    And the stdout output is captured and parsed (JSON or plain text)
    And the job status changes to "done"
    And the result is posted to the Slack thread via the proxy API

  Scenario: Worker does not pick up a job that is already processing
    Given the worker is running
    And a job with status "processing" exists in the database
    When the worker polls the database
    Then that job is not picked up again

  Scenario: Worker executes multiple pending jobs concurrently
    Given the worker is running with a max concurrency of 3
    And 3 jobs with status "pending" exist in the database
    When the worker polls the database
    Then all 3 jobs are executed concurrently across separate threads

  Scenario: Worker respects the configured concurrency limit
    Given the worker is running with a max concurrency of 2
    And 5 jobs with status "pending" exist in the database
    When the worker polls the database
    Then at most 2 jobs are picked up in a single poll cycle

  Scenario: Worker polls again after the configured interval
    Given the worker is running with a polling interval of 5 seconds
    And no pending jobs exist in the database
    When 5 seconds have elapsed
    Then the worker polls the database again

  Scenario: Worker restores trace_id from job record to logging context
    Given the worker is running
    And a job with status "pending" and trace_id "abc-123" exists in the database
    When the worker picks up the job
    Then the logging context contains trace_id "abc-123"
    And all log entries during job execution include trace_id "abc-123"

  Scenario: Worker handles command execution timeout as a temporary error
    Given the worker is running with a command timeout of 10 seconds
    And a job with status "pending" and command "alert" exists
    And the "chatops-alert" subprocess takes longer than the timeout
    When the worker executes the job
    Then the subprocess is terminated
    And the job is marked for retry (retry_count is incremented)
    And the job status is reset to "pending"

  Scenario: Worker handles non-zero exit code as a temporary error
    Given the worker is running
    And a job with status "pending" and command "alert" exists
    And the "chatops-alert" subprocess exits with code 1
    When the worker executes the job
    Then the job is marked for retry (retry_count is incremented)
    And the job status is reset to "pending"

  Scenario: Worker parses JSON output from command and extracts error information
    Given the worker is running
    And a job with status "pending" and command "alert" exists
    And the "chatops-alert" subprocess outputs: {"error": "Invalid host", "code": "ERR_001"}
    When the worker executes the job and parses the output as JSON
    Then the error information is extracted and posted to Slack
    And the job status is set to "failed" (user input error, not a temporary error)

  Scenario: Worker posts plain text output if command output is not JSON
    Given the worker is running
    And a job with status "pending" and command "alert" exists
    And the "chatops-alert" subprocess outputs: "Alert raised for web01"
    When the worker executes the job
    Then the plain text output is posted directly to Slack
    And the job status changes to "done"
