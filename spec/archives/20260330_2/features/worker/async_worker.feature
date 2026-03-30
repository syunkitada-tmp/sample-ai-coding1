Feature: Async Command Worker
  In order to execute commands without blocking the message reception API
  As the ChatOps framework
  I want a worker process to poll the database and execute pending jobs concurrently

  Scenario: Worker picks up a pending job and executes it successfully
    Given the worker is running
    And a job with status "pending" and command "alert" exists in the database
    When the worker polls the database
    Then the job status changes to "processing"
    And the command plugin for "alert" is executed
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
