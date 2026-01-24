import hashlib
import httpx
from behave import given, when, then, register_type
import parse


def md5_hash(password: str) -> str:
    """Convert raw password to MD5 hash (what KOReader sends)."""
    return hashlib.md5(password.encode()).hexdigest()


# Custom type for quoted strings
@parse.with_pattern(r'[^"]*')
def parse_quoted(text):
    return text


register_type(QuotedString=parse_quoted)


def table_to_dict(table):
    """Convert behave table to dictionary.

    Behave treats the first row as headings, so we need to include those too.
    """
    result = {}
    # First row is stored in headings
    if table.headings and len(table.headings) >= 2:
        result[table.headings[0].strip()] = table.headings[1].strip()
    # Remaining rows
    for row in table:
        if hasattr(row, 'cells') and len(row.cells) >= 2:
            result[row.cells[0].strip()] = row.cells[1].strip()
    return result


def get_auth_headers(context, username):
    """Get authentication headers for a user (password as MD5 hash)."""
    password = context.users.get(username, "readerpass")
    return {"x-auth-user": username, "x-auth-key": md5_hash(password)}


@given('user "{username}" has saved progress for document "{document}"')
def step_user_has_progress(context, username, document):
    data = table_to_dict(context.table)
    response = httpx.put(
        f"{context.base_url}/syncs/progress",
        headers=get_auth_headers(context, username),
        json={
            "document": document,
            "progress": data["progress"],
            "percentage": float(data["percentage"]),
            "device": data["device"],
            "device_id": data["device_id"],
        },
    )
    assert response.status_code == 200, f"Failed to save progress: {response.text}"


@when('user "{username}" updates progress for document "{document}"')
def step_update_progress(context, username, document):
    data = table_to_dict(context.table)
    context.last_response = httpx.put(
        f"{context.base_url}/syncs/progress",
        headers=get_auth_headers(context, username),
        json={
            "document": document,
            "progress": data["progress"],
            "percentage": float(data["percentage"]),
            "device": data["device"],
            "device_id": data["device_id"],
        },
    )


@when('user "{username}" retrieves progress for document "{document}"')
def step_retrieve_progress(context, username, document):
    context.last_response = httpx.get(
        f"{context.base_url}/syncs/progress/{document}",
        headers=get_auth_headers(context, username),
    )
    if context.last_response.status_code == 200:
        context.last_progress = context.last_response.json()


@when('I update progress without authentication for document "{document}"')
def step_update_no_auth(context, document):
    data = table_to_dict(context.table)
    context.last_response = httpx.put(
        f"{context.base_url}/syncs/progress",
        json={
            "document": document,
            "progress": data["progress"],
            "percentage": float(data["percentage"]),
            "device": data["device"],
            "device_id": data["device_id"],
        },
    )


@when('I retrieve progress without authentication for document "{document}"')
def step_retrieve_no_auth(context, document):
    context.last_response = httpx.get(f"{context.base_url}/syncs/progress/{document}")


@then("the progress update should succeed")
def step_progress_update_success(context):
    assert context.last_response.status_code == 200
    assert context.last_response.json()["status"] == "success"


@then('user "{username}" should have progress for document "{document}"')
def step_user_has_document_progress(context, username, document):
    response = httpx.get(
        f"{context.base_url}/syncs/progress/{document}",
        headers=get_auth_headers(context, username),
    )
    assert response.status_code == 200
    assert response.json()["document"] == document


@then("the progress should show")
def step_progress_shows(context):
    expected = table_to_dict(context.table)
    actual = context.last_progress

    if "progress" in expected:
        assert actual["progress"] == expected["progress"], \
            f"Expected progress {expected['progress']}, got {actual['progress']}"
    if "percentage" in expected:
        assert abs(actual["percentage"] - float(expected["percentage"])) < 0.001, \
            f"Expected percentage {expected['percentage']}, got {actual['percentage']}"
    if "device" in expected:
        assert actual["device"] == expected["device"], \
            f"Expected device {expected['device']}, got {actual['device']}"
    if "device_id" in expected:
        assert actual["device_id"] == expected["device_id"], \
            f"Expected device_id {expected['device_id']}, got {actual['device_id']}"


@then("the request should fail with status {status:d}")
def step_request_fail(context, status):
    assert context.last_response.status_code == status, \
        f"Expected status {status}, got {context.last_response.status_code}"
