Feature: MCP Use Functionality
  As a developer
  I want to test MCP functionality
  So that I can ensure reliable browser automation

  Scenario: Basic browser automation
    Given I have a browser automation task
    When I execute the automation
    Then it should complete successfully

  Scenario: Headless mode execution
    Given I have a browser automation task
    When I run it in headless mode
    Then it should complete without errors

  Scenario: Prompt utility functions
    Given I have a prompt template named "job_search"
    When I render it with variables
    Then I should get valid output

  Scenario: Task utility functions
    Given I have a synchronous task
    When I run it through task utils
    Then it should execute successfully
