Feature: Plugin-based Command Extension (Python Package Format)
  In order to add new commands without modifying the framework core
  As a developer
  I want to build and deploy Python command packages that are available as chatops-* executables from the PATH

  Scenario: Framework discovers a chatops-* executable from a deployed package in PATH
    Given the framework is running
    And a Python package "cmds/deploy/" with main.py is built and installed as "chatops-deploy" in PATH
    When the framework loads plugins by scanning PATH for chatops-* executables
    Then the command "deploy" is available for execution

  Scenario: A non-executable file in PATH is rejected at load time
    Given the framework is running
    And a file named "chatops-invalid" exists without execute permission
    When the framework loads plugins
    Then that file is not registered as a command
    And an error is logged indicating the file is not executable

  Scenario: Uninstalling a package makes the command unavailable after reload
    Given the command "deploy" is registered via a "chatops-deploy" executable (from cmds/deploy/ package)
    When the package is uninstalled (chatops-deploy removed from PATH) and the framework reloads plugins
    Then the command "deploy" is no longer available

  Scenario: Only files with chatops- prefix are recognized as commands
    Given the framework is running
    And an executable file named "other-command" (without chatops- prefix) exists in PATH
    When the framework loads plugins
    Then "other-command" is not registered as a command
    And only the chatops- prefixed executables are recognized
