import hashlib
import httpx
from behave import given, when, then


def md5_hash(password: str) -> str:
    """Convert raw password to MD5 hash (what KOReader sends)."""
    return hashlib.md5(password.encode()).hexdigest()


def get_auth_headers(context, username):
    """Get authentication headers for a user (password as MD5 hash)."""
    password = context.users.get(username, "readerpass")
    return {"x-auth-user": username, "x-auth-key": md5_hash(password)}


@when('user "{username}" lists all books')
def step_list_all_books(context, username):
    context.last_response = httpx.get(
        f"{context.base_url}/books",
        headers=get_auth_headers(context, username),
    )
    if context.last_response.status_code == 200:
        context.last_books = context.last_response.json()


@when('user "{username}" sets label "{label}" for book "{canonical_hash}"')
@given('user "{username}" sets label "{label}" for book "{canonical_hash}"')
def step_set_book_label(context, username, label, canonical_hash):
    context.last_response = httpx.put(
        f"{context.base_url}/books/label",
        headers=get_auth_headers(context, username),
        json={
            "canonical_hash": canonical_hash,
            "label": label,
        },
    )
    if context.last_response.status_code == 200:
        context.last_label_response = context.last_response.json()


@when('user "{username}" deletes label for book "{canonical_hash}"')
def step_delete_book_label(context, username, canonical_hash):
    context.last_response = httpx.delete(
        f"{context.base_url}/books/label/{canonical_hash}",
        headers=get_auth_headers(context, username),
    )


@when('I request the SVG card for user "{username}"')
def step_request_svg_card(context, username):
    context.last_response = httpx.get(f"{context.base_url}/card/{username}")


@when('I request the SVG card for user "{username}" with limit {limit:d}')
def step_request_svg_card_with_limit(context, username, limit):
    context.last_response = httpx.get(
        f"{context.base_url}/card/{username}",
        params={"limit": limit},
    )


@then("the response should succeed")
def step_response_success(context):
    assert context.last_response.status_code == 200, \
        f"Expected status 200, got {context.last_response.status_code}: {context.last_response.text}"


@then("the SVG response should succeed")
def step_svg_response_success(context):
    assert context.last_response.status_code == 200, \
        f"Expected status 200, got {context.last_response.status_code}: {context.last_response.text}"


@then("the books list should be empty")
def step_books_list_empty(context):
    assert len(context.last_books["books"]) == 0, \
        f"Expected empty list, got {len(context.last_books['books'])} books"


@then("the books list should have {count:d} books")
def step_books_list_count(context, count):
    assert len(context.last_books["books"]) == count, \
        f"Expected {count} books, got {len(context.last_books['books'])}"


@then('a book with hash "{canonical_hash}" should have percentage {percentage:f}')
def step_book_has_percentage(context, canonical_hash, percentage):
    books = context.last_books["books"]
    book = next((b for b in books if b["canonical_hash"] == canonical_hash), None)
    assert book is not None, f"Book with hash {canonical_hash} not found"
    assert abs(book["percentage"] - percentage) < 0.001, \
        f"Expected percentage {percentage}, got {book['percentage']}"


@then('a book with hash "{canonical_hash}" should have label "{label}"')
def step_book_has_label(context, canonical_hash, label):
    books = context.last_books["books"]
    book = next((b for b in books if b["canonical_hash"] == canonical_hash), None)
    assert book is not None, f"Book with hash {canonical_hash} not found"
    assert book["label"] == label, f"Expected label '{label}', got '{book['label']}'"


@then('a book with hash "{canonical_hash}" should have no label')
def step_book_has_no_label(context, canonical_hash):
    books = context.last_books["books"]
    book = next((b for b in books if b["canonical_hash"] == canonical_hash), None)
    assert book is not None, f"Book with hash {canonical_hash} not found"
    assert book["label"] is None, f"Expected no label, got '{book['label']}'"


@then('the label response should show "{label}"')
def step_label_response_shows(context, label):
    assert context.last_label_response["label"] == label, \
        f"Expected label '{label}', got '{context.last_label_response['label']}'"


@then('the response content type should be "{content_type}"')
def step_response_content_type(context, content_type):
    actual = context.last_response.headers.get("content-type", "")
    assert content_type in actual, \
        f"Expected content type '{content_type}', got '{actual}'"


@then('the SVG should contain "{text}"')
def step_svg_contains_text(context, text):
    svg_content = context.last_response.text
    assert text in svg_content, \
        f"Expected SVG to contain '{text}', but it doesn't. SVG content: {svg_content[:500]}"
