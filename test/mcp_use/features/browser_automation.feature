Feature: Browser Automation Functionality
  As a developer
  I want to test browser automation features
  So that I can ensure reliable MCP operations

  Scenario: Run basic browser automation
    Given I have a browser automation task
    When I execute the automation
    Then it should complete successfully

  Scenario: Headless mode execution
    Given I have a browser automation task
    When I run it in headless mode
    Then it should complete without errors

  Scenario: Visible mode execution
    Given I have a browser automation task
    When I run it in visible mode
    Then I should see browser activity
