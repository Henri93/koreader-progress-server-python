Feature: Progress Synchronization
  As a KOReader user
  I want to sync my reading progress
  So that I can continue reading on any device

  Background:
    Given a user "reader" with password "readerpass" exists

  Scenario: Save reading progress
    When user "reader" updates progress for document "book123"
      | progress   | /body/p[10]      |
      | percentage | 0.25             |
      | device     | Kindle Paperwhite|
      | device_id  | kindle-001       |
    Then the progress update should succeed
    And user "reader" should have progress for document "book123"

  Scenario: Progress is persisted and retrievable
    Given user "reader" has saved progress for document "novel456"
      | progress   | /body/chapter[5]/p[20] |
      | percentage | 0.50                   |
      | device     | Phone                  |
      | device_id  | phone-001              |
    When user "reader" retrieves progress for document "novel456"
    Then the progress should show
      | progress   | /body/chapter[5]/p[20] |
      | percentage | 0.50                   |
      | device     | Phone                  |
      | device_id  | phone-001              |

  Scenario: Progress syncs across devices
    Given user "reader" has saved progress for document "ebook789"
      | progress   | /body/p[100]     |
      | percentage | 0.30             |
      | device     | Kindle           |
      | device_id  | kindle-001       |
    When user "reader" updates progress for document "ebook789"
      | progress   | /body/p[200]     |
      | percentage | 0.60             |
      | device     | Phone            |
      | device_id  | phone-001        |
    And user "reader" retrieves progress for document "ebook789"
    Then the progress should show
      | progress   | /body/p[200]     |
      | percentage | 0.60             |
      | device     | Phone            |
      | device_id  | phone-001        |

  Scenario: Unknown document returns 404
    When user "reader" retrieves progress for document "nonexistent"
    Then the request should fail with status 404
