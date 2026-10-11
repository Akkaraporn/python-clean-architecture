"""Dependency contracts for the HTTP layer.

Handlers declare *what* they need (a use case, the token service) through these
providers; *how* each one is built (which repository, which database session)
is decided once in the composition root, which binds them with
``app.dependency_overrides``. This keeps handlers free of SQLAlchemy and of any
concrete adapter, and lets tests swap any piece the same way.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.domain.errors import InvalidTokenError
from src.usecases import GetCurrentUser, LoginUser, RegisterUser
from src.usecases.ports import TokenService


def _not_wired(name: str) -> NotImplementedError:
    return NotImplementedError(f"{name} is not wired; bind it in the composition root")


def provide_register_user() -> RegisterUser:
    raise _not_wired("RegisterUser")


def provide_login_user() -> LoginUser:
    raise _not_wired("LoginUser")


def provide_get_current_user() -> GetCurrentUser:
    raise _not_wired("GetCurrentUser")


def provide_token_service() -> TokenService:
    raise _not_wired("TokenService")


# auto_error=False: a missing header goes through the same 401 path as a bad token,
# instead of FastAPI's default 403.
bearer_scheme = HTTPBearer(auto_error=False, description="Access token from /api/auth/login")


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    tokens: Annotated[TokenService, Depends(provide_token_service)],
) -> UUID:
    if credentials is None:
        raise InvalidTokenError("Missing bearer token")
    return tokens.decode(credentials.credentials)


RegisterUserDep = Annotated[RegisterUser, Depends(provide_register_user)]
LoginUserDep = Annotated[LoginUser, Depends(provide_login_user)]
GetCurrentUserDep = Annotated[GetCurrentUser, Depends(provide_get_current_user)]
CurrentUserId = Annotated[UUID, Depends(get_current_user_id)]
