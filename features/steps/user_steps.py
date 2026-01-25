import hashlib
import httpx
from behave import given, when, then


def md5_hash(password: str) -> str:
    """Convert raw password to MD5 hash (what KOReader sends)."""
    return hashlib.md5(password.encode()).hexdigest()


@given('a user "{username}" with password "{password}" exists')
def step_create_user(context, username, password):
    response = httpx.post(
        f"{context.base_url}/users/create",
        json={"username": username, "password": md5_hash(password)},
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    context.users[username] = password


@when('I register with username "{username}" and password "{password}"')
def step_register(context, username, password):
    context.last_response = httpx.post(
        f"{context.base_url}/users/create",
        json={"username": username, "password": md5_hash(password)},
    )
    if context.last_response.status_code == 201:
        context.users[username] = password


@when('I register with empty username and password "{password}"')
def step_register_empty_username(context, password):
    context.last_response = httpx.post(
        f"{context.base_url}/users/create",
        json={"username": "", "password": password},
    )


@then("the registration should succeed")
def step_registration_success(context):
    assert context.last_response.status_code == 201
    assert context.last_response.json()["status"] == "success"


@then("the registration should fail with status {status:d}")
def step_registration_fail(context, status):
    assert context.last_response.status_code == status


@then('I should be able to authenticate with username "{username}" and password "{password}"')
def step_can_authenticate(context, username, password):
    response = httpx.get(
        f"{context.base_url}/users/auth",
        headers={"x-auth-user": username, "x-auth-key": md5_hash(password)},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"


@when('I authenticate with username "{username}" and password "{password}"')
def step_authenticate(context, username, password):
    context.last_response = httpx.get(
        f"{context.base_url}/users/auth",
        headers={"x-auth-user": username, "x-auth-key": md5_hash(password)},
    )


@when("I authenticate without credentials")
def step_authenticate_no_creds(context):
    context.last_response = httpx.get(f"{context.base_url}/users/auth")


@then("the authentication should succeed")
def step_auth_success(context):
    assert context.last_response.status_code == 200
    assert context.last_response.json()["status"] == "authenticated"


@then("the authentication should fail with status {status:d}")
def step_auth_fail(context, status):
    assert context.last_response.status_code == status
