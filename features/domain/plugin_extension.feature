Feature: Plugin-based Command Extension
  In order to add new commands without modifying the framework core
  As a developer
  I want the framework to automatically discover and register plugins placed in the plugin directory

  Scenario: Framework discovers a new plugin placed in the plugin directory
    Given the framework is running
    And a plugin file defining command "deploy" is placed in the plugin directory
    When the framework loads plugins
    Then the command "deploy" is available for execution

  Scenario: Plugin without a required interface field is rejected at load time
    Given the framework is running
    And a plugin file is placed in the plugin directory without a "command_name" field
    When the framework loads plugins
    Then that plugin is not registered
    And an error is logged indicating the missing field

  Scenario: Removing a plugin file makes the command unavailable after reload
    Given the command "deploy" is registered via a plugin
    When the plugin file for "deploy" is removed and the framework reloads plugins
    Then the command "deploy" is no longer available

  Scenario Outline: Plugin interface must define all required fields
    Given a plugin file is placed in the plugin directory missing the "<field>" field
    When the framework loads plugins
    Then that plugin is rejected with a missing-field error for "<field>"

    Examples:
      | field        |
      | command_name |
      | description  |
      | execute      |
