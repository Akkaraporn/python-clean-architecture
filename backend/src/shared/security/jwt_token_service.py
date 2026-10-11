from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from src.domain.errors import ExpiredTokenError, InvalidTokenError
from src.usecases.ports import TokenService

ACCESS_TOKEN_TYPE = "access"


def _utc_now() -> datetime:
    return datetime.now(UTC)


class JwtTokenService(TokenService):
    def __init__(
        self,
        secret: str,
        expire_minutes: int,
        algorithm: str = "HS256",
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._secret = secret
        self._expire = timedelta(minutes=expire_minutes)
        self._algorithm = algorithm
        self._clock = clock

    def create_access_token(self, user_id: UUID) -> str:
        issued_at = self._clock()
        # The payload is only signed, not encrypted: keep it to non-sensitive claims.
        payload = {
            "sub": str(user_id),
            "type": ACCESS_TOKEN_TYPE,
            "iat": issued_at,
            "exp": issued_at + self._expire,
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> UUID:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                # Pin the accepted algorithm instead of trusting the token header,
                # which rules out "none" and algorithm-confusion attacks.
                algorithms=[self._algorithm],
                options={"require": ["sub", "exp", "iat"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ExpiredTokenError() from exc
        except jwt.InvalidTokenError as exc:
            raise InvalidTokenError() from exc

        # Reserves room for other token kinds (e.g. refresh) that must not grant access.
        if payload.get("type") != ACCESS_TOKEN_TYPE:
            raise InvalidTokenError()
        try:
            return UUID(payload["sub"])
        except (TypeError, ValueError) as exc:
            raise InvalidTokenError() from exc
