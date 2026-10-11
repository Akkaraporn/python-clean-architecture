from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import Settings
from src.domain.entities import User
from src.infrastructure.fastapi.main import create_app, get_password_hasher
from src.interface.repositories.postgres import PostgresUserRepository
from src.shared.security import BcryptPasswordHasher, JwtTokenService

JWT_SECRET = "api-test-secret-that-is-long-enough-for-hs256"
PASSWORD = "s3cret-pass"
ALLOWED_ORIGIN = "http://localhost:5173"

# One instance for the whole run: minimum bcrypt cost keeps the suite fast, and a
# stable instance lets LoginUser reuse its cached dummy hash.
FAST_HASHER = BcryptPasswordHasher(rounds=4)


@pytest.fixture
def settings(db_engine: Engine) -> Settings:
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url=db_engine.url.render_as_string(hide_password=False),
        jwt_secret=JWT_SECRET,
        jwt_expire_minutes=30,
        cors_origins=[ALLOWED_ORIGIN],
    )


@pytest.fixture
def app(settings: Settings, test_session_factory: sessionmaker[Session]) -> FastAPI:
    app = create_app(settings)
    # Real wiring, two test seams: requests share the test transaction (rolled back
    # after each test), and password hashing is cheap.
    app.state.session_factory = test_session_factory
    app.dependency_overrides[get_password_hasher] = lambda: FAST_HASHER
    return app


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def tokens() -> JwtTokenService:
    return JwtTokenService(secret=JWT_SECRET, expire_minutes=30)


@pytest.fixture
def register(client: TestClient) -> Callable[..., Any]:
    def _register(
        email: str = "jane@example.com", password: str = PASSWORD, full_name: str = "Jane Doe"
    ) -> dict[str, Any]:
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture
def login(client: TestClient) -> Callable[..., str]:
    def _login(email: str = "jane@example.com", password: str = PASSWORD) -> str:
        response = client.post("/api/auth/login", json={"email": email, "password": password})
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    return _login


@pytest.fixture
def inactive_user(db_session: Session) -> User:
    user = User.create(
        email="gone@example.com", hashed_password=FAST_HASHER.hash(PASSWORD), full_name="Gone"
    )
    user.deactivate()
    return PostgresUserRepository(db_session).add(user)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
