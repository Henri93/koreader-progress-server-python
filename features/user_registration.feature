Feature: User Registration
  As a KOReader user
  I want to register an account
  So that I can sync my reading progress

  Scenario: Register a new user
    When I register with username "newuser" and password "secret123"
    Then the registration should succeed
    And I should be able to authenticate with username "newuser" and password "secret123"

  Scenario: Cannot register duplicate username
    Given a user "existinguser" with password "pass123" exists
    When I register with username "existinguser" and password "differentpass"
    Then the registration should fail with status 402

  Scenario: Registration requires username and password
    When I register with empty username and password "somepass"
    Then the registration should fail with status 400
