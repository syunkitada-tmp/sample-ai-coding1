Feature: Job Retry Mechanism
  In order to recover from transient command failures
  As the ChatOps framework
  I want to automatically retry failed jobs up to a configured limit

  Scenario: Failed job is scheduled for retry within the limit
    Given the worker is running with a max retry count of 3
    And a job with status "processing" and retry_count 0 exists
    When the command execution fails
    Then the job status is set back to "pending"
    And the retry_count is incremented to 1
    And the failure reason is recorded on the job record
    And retry_after is set to a future timestamp

  Scenario: Failed job is not picked up before retry_after
    Given a job with status "pending" and a retry_after in the future exists
    When the worker polls the database
    Then that job is not picked up

  Scenario: Failed job is picked up after retry_after has passed
    Given a job with status "pending" and a retry_after in the past exists
    When the worker polls the database
    Then that job is picked up and executed

  Scenario: Job exceeding the retry limit is marked as failed and notified
    Given the worker is running with a max retry count of 3
    And a job with status "processing" and retry_count 3 exists
    When the command execution fails
    Then the job status is set to "failed"
    And a final failure notification is posted to the Slack thread
    And no further retry is attempted

  Scenario Outline: Retry count boundary behaviour
    Given the worker is running with a max retry count of 3
    And a job with status "processing" and retry_count <count> exists
    When the command execution fails
    Then the job outcome is "<outcome>"

    Examples:
      | count | outcome            |
      | 0     | retried            |
      | 2     | retried            |
      | 3     | permanently failed |
