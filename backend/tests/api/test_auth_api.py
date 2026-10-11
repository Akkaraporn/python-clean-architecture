"""HTTP contract of the auth endpoints: status codes, JSON shape and headers.

Business rules are covered by the use-case unit tests; these tests check that the
request reaches the right use case through the real wiring and that each outcome
is reported correctly over HTTP.
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from src.domain.entities import User
from tests.api.conftest import PASSWORD

pytestmark = pytest.mark.integration

USER_FIELDS = {"id", "email", "full_name", "is_active", "created_at"}


# --- POST /api/auth/register -------------------------------------------------------


def test_register_returns_201_and_the_public_user(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "Jane@Example.com", "password": PASSWORD, "full_name": "Jane Doe"},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == USER_FIELDS
    assert UUID(body["id"])
    assert body["email"] == "jane@example.com"
    assert body["full_name"] == "Jane Doe"
    assert body["is_active"] is True


def test_register_never_exposes_the_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"email": "jane@example.com", "password": PASSWORD, "full_name": "Jane"},
    )

    assert "password" not in response.text
    assert "$2b$" not in response.text


@pytest.mark.parametrize("email", ["jane@example.com", "JANE@example.COM"])
def test_register_duplicate_email_returns_409(
    client: TestClient, register: Callable[..., dict[str, Any]], email: str
) -> None:
    register()

    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "another-pass", "full_name": "Impostor"},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "user_already_exists"


def test_failed_register_does_not_break_the_next_request(
    client: TestClient, register: Callable[..., dict[str, Any]]
) -> None:
    register()
    assert (
        client.post(
            "/api/auth/register",
            json={"email": "jane@example.com", "password": PASSWORD, "full_name": "Again"},
        ).status_code
        == 409
    )

    register(email="john@example.com")


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "not-an-email", "password": PASSWORD, "full_name": "J"}, "email"),
        ({"email": "jane@example.com", "password": "short", "full_name": "J"}, "password"),
        # 25 Thai characters are 75 bytes in UTF-8: over bcrypt's 72-byte limit.
        ({"email": "jane@example.com", "password": "ก" * 25, "full_name": "J"}, "password"),
        ({"email": "jane@example.com", "password": PASSWORD, "full_name": "   "}, "full_name"),
        ({"email": "jane@example.com", "password": PASSWORD}, "full_name"),
    ],
    ids=["bad-email", "short-password", "password-over-72-bytes", "blank-name", "missing-name"],
)
def test_register_invalid_input_returns_422(
    client: TestClient, payload: dict[str, str], field: str
) -> None:
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    assert [error["loc"] for error in response.json()["detail"]] == [["body", field]]


# --- POST /api/auth/login ----------------------------------------------------------


def test_login_returns_a_bearer_token(
    client: TestClient, register: Callable[..., dict[str, Any]]
) -> None:
    register()

    response = client.post(
        "/api/auth/login", json={"email": "JANE@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"


@pytest.mark.parametrize(
    ("email", "password"),
    [("jane@example.com", "wrong-password"), ("nobody@example.com", PASSWORD)],
    ids=["wrong-password", "unknown-email"],
)
def test_login_bad_credentials_returns_401(
    client: TestClient, register: Callable[..., dict[str, Any]], email: str, password: str
) -> None:
    register()

    response = client.post("/api/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    # Identical bodies, so the API cannot be used to discover registered emails.
    assert response.json() == {
        "detail": "Invalid email or password",
        "code": "invalid_credentials",
    }


def test_login_inactive_user_returns_403(client: TestClient, inactive_user: User) -> None:
    response = client.post(
        "/api/auth/login", json={"email": inactive_user.email, "password": PASSWORD}
    )

    assert response.status_code == 403
    assert response.json()["code"] == "inactive_user"


@pytest.mark.parametrize(
    "payload",
    [{"email": "jane@example.com"}, {"email": "bad", "password": "x"}, {}],
    ids=["missing-password", "bad-email", "empty"],
)
def test_login_invalid_input_returns_422(client: TestClient, payload: dict[str, str]) -> None:
    assert client.post("/api/auth/login", json=payload).status_code == 422
