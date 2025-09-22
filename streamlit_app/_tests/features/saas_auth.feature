Feature: User authentication and credit-based access in Streamlit app

  Background:
    Given the Streamlit app is running
    And the backend API is available at "https://api.saasidea.com"

  Scenario: Redirect to login when not authenticated
    Given the user is not logged in
    When the user accesses a protected page
    Then the app redirects to "https://api.saasidea.com/login"
    And the user is returned with a valid token

  Scenario: Store authentication token
    Given the user has logged in successfully
    When the backend redirects back with a token
    Then the app stores the token in session state
    And the token is used for all API requests

  Scenario: Display credit balance
    Given the user is authenticated
    When the app calls "/entitlements"
    Then the user’s credit balance is displayed on the dashboard

  Scenario: Restrict feature if no credits
    Given the user is authenticated
    And the user’s credit balance is 0
    When the user clicks on "Generate Report"
    Then the button is disabled
    And the app shows "You need credits to use this feature"

  Scenario: Allow feature if credits available
    Given the user is authenticated
    And the user’s credit balance is greater than 0
    When the user clicks on "Generate Report"
    Then the request is sent to the backend with the token
    And the report is generated successfully
