from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest

from src.domain.errors import ExpiredTokenError, InvalidTokenError
from src.shared.security import JwtTokenService

SECRET = "test-secret-that-is-long-enough-for-hs256"
OTHER_SECRET = "another-secret-that-is-long-enough-for-hs256"


@pytest.fixture
def service() -> JwtTokenService:
    return JwtTokenService(secret=SECRET, expire_minutes=30)


def claims_of(token: str) -> dict[str, object]:
    return jwt.decode(token, options={"verify_signature": False})


def test_round_trip_returns_the_user_id(service: JwtTokenService) -> None:
    user_id = uuid4()

    assert service.decode(service.create_access_token(user_id)) == user_id


def test_payload_carries_only_non_sensitive_claims(service: JwtTokenService) -> None:
    claims = claims_of(service.create_access_token(uuid4()))

    assert set(claims) == {"sub", "type", "iat", "exp"}


def test_expiry_follows_configured_minutes() -> None:
    issued_at = datetime(2030, 1, 1, tzinfo=UTC)
    service = JwtTokenService(secret=SECRET, expire_minutes=15, clock=lambda: issued_at)

    claims = claims_of(service.create_access_token(uuid4()))

    assert claims["iat"] == int(issued_at.timestamp())
    assert claims["exp"] == int((issued_at + timedelta(minutes=15)).timestamp())


def test_expired_token_is_rejected() -> None:
    an_hour_ago = datetime.now(UTC) - timedelta(hours=1)
    issuer = JwtTokenService(secret=SECRET, expire_minutes=30, clock=lambda: an_hour_ago)
    token = issuer.create_access_token(uuid4())

    with pytest.raises(ExpiredTokenError):
        JwtTokenService(secret=SECRET, expire_minutes=30).decode(token)


def test_expired_error_is_still_an_invalid_token_error() -> None:
    assert issubclass(ExpiredTokenError, InvalidTokenError)


def test_tampered_payload_is_rejected(service: JwtTokenService) -> None:
    header, _, signature = service.create_access_token(uuid4()).split(".")
    forged_payload = jwt.encode(
        {"sub": str(uuid4()), "type": "access", "iat": 0, "exp": 9999999999}, "x" * 32
    ).split(".")[1]

    with pytest.raises(InvalidTokenError):
        service.decode(f"{header}.{forged_payload}.{signature}")


def test_token_signed_with_another_secret_is_rejected(service: JwtTokenService) -> None:
    token = JwtTokenService(secret=OTHER_SECRET, expire_minutes=30).create_access_token(uuid4())

    with pytest.raises(InvalidTokenError):
        service.decode(token)


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c", "a.b"])
def test_malformed_token_is_rejected(service: JwtTokenService, token: str) -> None:
    with pytest.raises(InvalidTokenError):
        service.decode(token)


def test_unsigned_none_algorithm_token_is_rejected(service: JwtTokenService) -> None:
    token = jwt.encode(
        {"sub": str(uuid4()), "type": "access", "iat": 0, "exp": 9999999999},
        key=None,
        algorithm="none",
    )

    with pytest.raises(InvalidTokenError):
        service.decode(token)


def test_token_with_unexpected_algorithm_is_rejected(service: JwtTokenService) -> None:
    long_secret = SECRET * 2  # HS512 wants a 64-byte key
    service = JwtTokenService(secret=long_secret, expire_minutes=30)
    token = JwtTokenService(
        secret=long_secret, expire_minutes=30, algorithm="HS512"
    ).create_access_token(uuid4())

    with pytest.raises(InvalidTokenError):
        service.decode(token)


@pytest.mark.parametrize(
    "payload",
    [
        {"type": "access", "iat": 0, "exp": 9999999999},
        {"sub": "not-a-uuid", "type": "access", "iat": 0, "exp": 9999999999},
        {"sub": str(UUID(int=1)), "type": "refresh", "iat": 0, "exp": 9999999999},
        {"sub": str(UUID(int=1)), "iat": 0, "exp": 9999999999},
        {"sub": str(UUID(int=1)), "type": "access", "iat": 0},
    ],
    ids=["missing-sub", "non-uuid-sub", "wrong-type", "missing-type", "missing-exp"],
)
def test_token_with_bad_claims_is_rejected(
    service: JwtTokenService, payload: dict[str, object]
) -> None:
    token = jwt.encode(payload, SECRET, algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        service.decode(token)
