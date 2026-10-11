import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config.settings import Settings
from tests.api.conftest import ALLOWED_ORIGIN, JWT_SECRET

pytestmark = pytest.mark.integration


def preflight(client: TestClient, origin: str) -> dict[str, str]:
    response = client.options(
        "/api/users/me",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    return dict(response.headers)


def test_preflight_from_allowed_origin_is_accepted(client: TestClient) -> None:
    headers = preflight(client, ALLOWED_ORIGIN)

    assert headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert "authorization" in headers["access-control-allow-headers"].lower()
    # No credentials: tokens go in a header, never in cookies.
    assert "access-control-allow-credentials" not in headers


def test_preflight_from_unknown_origin_is_not_allowed(client: TestClient) -> None:
    headers = preflight(client, "http://evil.example.com")

    assert "access-control-allow-origin" not in headers


def test_simple_request_from_allowed_origin_gets_cors_header(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN


def test_startup_log_hides_secrets(
    app: FastAPI, settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    db_password = settings.database_url.hosts()[0]["password"]

    with caplog.at_level(logging.INFO, logger="src"), TestClient(app):
        pass

    startup = next(r.getMessage() for r in caplog.records if r.getMessage().startswith("Starting"))
    assert "***" in startup
    assert ALLOWED_ORIGIN in startup
    for secret in (db_password, JWT_SECRET):
        assert secret
        assert secret not in caplog.text


def test_openapi_describes_the_api(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert schema["info"]["description"]
    assert {tag["name"] for tag in schema["tags"]} == {"auth", "users", "health"}
