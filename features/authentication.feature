Feature: User Authentication
  As a KOReader user
  I want to authenticate with the server
  So that I can access my reading progress securely

  Scenario: Authenticate with valid credentials
    Given a user "authuser" with password "authpass" exists
    When I authenticate with username "authuser" and password "authpass"
    Then the authentication should succeed

  Scenario: Reject invalid password
    Given a user "testuser" with password "correctpass" exists
    When I authenticate with username "testuser" and password "wrongpass"
    Then the authentication should fail with status 401

  Scenario: Reject unknown username
    When I authenticate with username "unknownuser" and password "anypass"
    Then the authentication should fail with status 401

  Scenario: Reject missing credentials
    When I authenticate without credentials
    Then the authentication should fail with status 401
