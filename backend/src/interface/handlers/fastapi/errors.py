"""Translates domain errors into HTTP responses in one place, so routes stay free
of try/except and every endpoint reports the same error the same way."""

from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.domain.errors import (
    DomainError,
    ExpiredTokenError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


@dataclass(frozen=True)
class ErrorMapping:
    status_code: int
    code: str
    headers: dict[str, str] | None = None


BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}
INVALID_TOKEN_CHALLENGE = {"WWW-Authenticate": 'Bearer error="invalid_token"'}

# Looked up along the exception's MRO, so the most specific entry wins
# (ExpiredTokenError over InvalidTokenError) and new subclasses inherit a mapping.
ERROR_MAPPINGS: dict[type[DomainError], ErrorMapping] = {
    UserAlreadyExistsError: ErrorMapping(status.HTTP_409_CONFLICT, "user_already_exists"),
    InvalidCredentialsError: ErrorMapping(
        status.HTTP_401_UNAUTHORIZED, "invalid_credentials", BEARER_CHALLENGE
    ),
    ExpiredTokenError: ErrorMapping(
        status.HTTP_401_UNAUTHORIZED, "token_expired", INVALID_TOKEN_CHALLENGE
    ),
    InvalidTokenError: ErrorMapping(
        status.HTTP_401_UNAUTHORIZED, "invalid_token", INVALID_TOKEN_CHALLENGE
    ),
    # Reached only with a valid token whose account no longer exists: the credential
    # is no longer good, so the client should authenticate again.
    UserNotFoundError: ErrorMapping(
        status.HTTP_401_UNAUTHORIZED, "user_not_found", INVALID_TOKEN_CHALLENGE
    ),
    InactiveUserError: ErrorMapping(status.HTTP_403_FORBIDDEN, "inactive_user"),
}
FALLBACK = ErrorMapping(status.HTTP_400_BAD_REQUEST, "domain_error")


def mapping_for(exc: DomainError) -> ErrorMapping:
    for cls in type(exc).__mro__:
        if cls in ERROR_MAPPINGS:
            return ERROR_MAPPINGS[cls]
    return FALLBACK


async def handle_domain_error(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    mapping = mapping_for(exc)
    return JSONResponse(
        status_code=mapping.status_code,
        content={"detail": str(exc), "code": mapping.code},
        headers=mapping.headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
