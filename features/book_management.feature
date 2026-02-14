Feature: Book Management
  As a user of the progress server
  I want to manage my books with labels and view them all at once
  So that I can easily track my reading progress

  Background:
    Given a user "reader" with password "readerpass" exists

  Scenario: List books returns empty when no progress
    When user "reader" lists all books
    Then the response should succeed
    And the books list should be empty

  Scenario: List books shows books with progress
    Given user "reader" has saved progress for document "book1"
      | progress   | /body/p[10] |
      | percentage | 0.25        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    And user "reader" has saved progress for document "book2"
      | progress   | /body/p[50] |
      | percentage | 0.50        |
      | device     | Phone       |
      | device_id  | phone-001   |
    When user "reader" lists all books
    Then the response should succeed
    And the books list should have 2 books
    And a book with hash "book1" should have percentage 0.25
    And a book with hash "book2" should have percentage 0.50

  Scenario: Set book label
    Given user "reader" has saved progress for document "mybook"
      | progress   | /body/p[10] |
      | percentage | 0.25        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    When user "reader" sets label "The Great Gatsby" for book "mybook"
    Then the response should succeed
    And the label response should show "The Great Gatsby"

  Scenario: Book label appears in book list
    Given user "reader" has saved progress for document "labeledbook"
      | progress   | /body/p[10] |
      | percentage | 0.25        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    And user "reader" sets label "My Favorite Book" for book "labeledbook"
    When user "reader" lists all books
    Then the response should succeed
    And a book with hash "labeledbook" should have label "My Favorite Book"

  Scenario: Delete book label
    Given user "reader" has saved progress for document "bookwithlabel"
      | progress   | /body/p[10] |
      | percentage | 0.25        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    And user "reader" sets label "Temporary Label" for book "bookwithlabel"
    When user "reader" deletes label for book "bookwithlabel"
    Then the response should succeed
    When user "reader" lists all books
    Then a book with hash "bookwithlabel" should have no label

  Scenario: Setting label for non-existent book fails
    When user "reader" sets label "Some Label" for book "nonexistent"
    Then the request should fail with status 404

  Scenario: Deleting non-existent label fails
    Given user "reader" has saved progress for document "unlabeledbook"
      | progress   | /body/p[10] |
      | percentage | 0.25        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    When user "reader" deletes label for book "unlabeledbook"
    Then the request should fail with status 404

  Scenario: SVG card returns valid SVG for user with books
    Given user "reader" has saved progress for document "svgbook"
      | progress   | /body/p[50] |
      | percentage | 0.50        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    When I request the SVG card for user "reader"
    Then the SVG response should succeed
    And the response content type should be "image/svg+xml"
    And the SVG should contain "Currently Reading"

  Scenario: SVG card returns valid SVG for user with no books
    When I request the SVG card for user "reader"
    Then the SVG response should succeed
    And the response content type should be "image/svg+xml"
    And the SVG should contain "No books in progress"

  Scenario: SVG card returns 404 for non-existent user
    When I request the SVG card for user "unknownuser"
    Then the request should fail with status 404

  Scenario: SVG card respects limit parameter
    Given user "reader" has saved progress for document "svgbook1"
      | progress   | /body/p[10] |
      | percentage | 0.10        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    And user "reader" has saved progress for document "svgbook2"
      | progress   | /body/p[20] |
      | percentage | 0.20        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    And user "reader" has saved progress for document "svgbook3"
      | progress   | /body/p[30] |
      | percentage | 0.30        |
      | device     | Kindle      |
      | device_id  | kindle-001  |
    When I request the SVG card for user "reader" with limit 2
    Then the SVG response should succeed
