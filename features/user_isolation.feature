Feature: User Data Isolation
  As a KOReader user
  I want my reading progress to be private
  So that other users cannot see or modify my data

  Background:
    Given a user "alice" with password "alicepass" exists
    And a user "bob" with password "bobpass" exists

  Scenario: Users have independent progress for the same book
    Given user "alice" has saved progress for document "shared-book"
      | progress   | /body/p[50]      |
      | percentage | 0.25             |
      | device     | Alice Kindle     |
      | device_id  | alice-kindle     |
    And user "bob" has saved progress for document "shared-book"
      | progress   | /body/p[150]     |
      | percentage | 0.75             |
      | device     | Bob Phone        |
      | device_id  | bob-phone        |
    When user "alice" retrieves progress for document "shared-book"
    Then the progress should show
      | progress   | /body/p[50]      |
      | percentage | 0.25             |
    When user "bob" retrieves progress for document "shared-book"
    Then the progress should show
      | progress   | /body/p[150]     |
      | percentage | 0.75             |

  Scenario: User cannot see another user's books
    Given user "alice" has saved progress for document "alice-private-book"
      | progress   | /body/p[10]      |
      | percentage | 0.10             |
      | device     | Alice Device     |
      | device_id  | alice-device     |
    When user "bob" retrieves progress for document "alice-private-book"
    Then the request should fail with status 404

  Scenario: Authentication required to update progress
    When I update progress without authentication for document "anybook"
      | progress   | /body/p[1]       |
      | percentage | 0.01             |
      | device     | Hacker Device    |
      | device_id  | hacker-001       |
    Then the request should fail with status 401

  Scenario: Authentication required to retrieve progress
    Given user "alice" has saved progress for document "protected-book"
      | progress   | /body/p[100]     |
      | percentage | 0.50             |
      | device     | Device           |
      | device_id  | device-001       |
    When I retrieve progress without authentication for document "protected-book"
    Then the request should fail with status 401
