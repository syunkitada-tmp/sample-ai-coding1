Feature: Help Command
  In order to discover available commands
  As an operator
  I want to send "!help" in Slack and receive a plain-text list of all registered commands

  Scenario: Help returns a list of all registered commands
    Given the plugins "alert" and "deploy" are registered with descriptions
    When a POST request is received with text "!help"
    Then a job with command "help" and status "pending" is created
    And the worker executes the help job
    And the Slack thread receives a plain-text reply listing all commands and their descriptions

  Scenario: Help reply format is "!command_name: description" per line
    Given the plugin "alert" is registered with description "Analyze alert logs"
    And the plugin "deploy" is registered with description "Deploy application"
    When the help command is executed
    Then the reply contains "!alert: Analyze alert logs"
    And the reply contains "!deploy: Deploy application"

  Scenario: Help returns a message when no plugins are registered
    Given no plugins are registered
    When the help command is executed
    Then the Slack thread receives a reply stating no commands are available
