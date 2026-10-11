from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.domain.entities import User
from src.shared.security import JwtTokenService
from tests.api.conftest import JWT_SECRET, bearer

pytestmark = pytest.mark.integration

INVALID_TOKEN_CHALLENGE = 'Bearer error="invalid_token"'


def test_me_returns_the_token_owner(
    client: TestClient,
    register: Callable[..., dict[str, Any]],
    login: Callable[..., str],
) -> None:
    registered = register()

    response = client.get("/api/users/me", headers=bearer(login()))

    assert response.status_code == 200
    assert response.json() == registered


def test_me_without_a_token_returns_401(client: TestClient) -> None:
    response = client.get("/api/users/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.parametrize(
    "authorization",
    ["Bearer not-a-jwt", "Bearer a.b.c", "Basic dXNlcjpwYXNz", "Bearer"],
    ids=["garbage", "malformed-jwt", "wrong-scheme", "empty-bearer"],
)
def test_me_with_an_unusable_header_returns_401(client: TestClient, authorization: str) -> None:
    response = client.get("/api/users/me", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"].startswith("Bearer")


def test_me_with_a_tampered_token_returns_401(
    client: TestClient, register: Callable[..., dict[str, Any]], login: Callable[..., str]
) -> None:
    register()
    header, payload, signature = login().split(".")
    tampered = f"{header}.{payload}.{signature[::-1]}"

    response = client.get("/api/users/me", headers=bearer(tampered))

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == INVALID_TOKEN_CHALLENGE
    assert response.json()["code"] == "invalid_token"


def test_me_with_a_token_signed_by_another_key_returns_401(
    client: TestClient, register: Callable[..., dict[str, Any]]
) -> None:
    user_id = register()["id"]
    forged = JwtTokenService(secret="z" * 48, expire_minutes=30).create_access_token(user_id)

    response = client.get("/api/users/me", headers=bearer(forged))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"


def test_me_with_an_expired_token_returns_401(
    client: TestClient, register: Callable[..., dict[str, Any]]
) -> None:
    user_id = register()["id"]
    an_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    expired = JwtTokenService(
        secret=JWT_SECRET, expire_minutes=30, clock=lambda: an_hour_ago
    ).create_access_token(user_id)

    response = client.get("/api/users/me", headers=bearer(expired))

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == INVALID_TOKEN_CHALLENGE
    assert response.json() == {"detail": "Token has expired", "code": "token_expired"}


def test_me_for_an_account_that_no_longer_exists_returns_401(
    client: TestClient, tokens: JwtTokenService
) -> None:
    response = client.get("/api/users/me", headers=bearer(tokens.create_access_token(uuid4())))

    assert response.status_code == 401
    assert response.json()["code"] == "user_not_found"


def test_me_for_a_deactivated_account_returns_403(
    client: TestClient, tokens: JwtTokenService, inactive_user: User
) -> None:
    response = client.get(
        "/api/users/me", headers=bearer(tokens.create_access_token(inactive_user.id))
    )

    assert response.status_code == 403
    assert response.json()["code"] == "inactive_user"


# --- GET /health -------------------------------------------------------------------


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
