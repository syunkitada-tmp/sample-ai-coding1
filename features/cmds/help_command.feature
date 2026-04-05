Feature: Help Command
  In order to discover available commands
  As an operator
  I want to send "!help" in Slack and receive a plain-text list of all registered shell commands

  Scenario: Help returns a list of all registered shell commands
    Given the "chatops-help" shell command is executable
    And executable shell commands "chatops-alert" and "chatops-deploy" are available with descriptions
    When a POST request is received with text "!help"
    Then a job with command "help" and status "pending" is created
    And the worker executes the help job via subprocess
    And the "chatops-help" command scans available "chatops-*" files and returns their list
    And the Slack thread receives a plain-text reply listing all commands and their descriptions

  Scenario: Help reply format is "!command_name: description" per line
    Given the "chatops-help" shell command is executable
    And "chatops-alert" is available with description "Analyze alert logs"
    And "chatops-deploy" is available with description "Deploy application"
    When the help command is executed via subprocess
    Then the reply contains "!alert: Analyze alert logs"
    And the reply contains "!deploy: Deploy application"

  Scenario: Help returns a message when no shell commands are registered
    Given the "chatops-help" shell command is executable
    And no "chatops-*" executable files exist in the plugin directory
    When the help command is executed via subprocess
    Then the Slack thread receives a reply stating no commands are available
