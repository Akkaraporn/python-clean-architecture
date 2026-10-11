"""Composition root: the only module that knows every layer and wires them together.

Run with:  uvicorn src.infrastructure.fastapi.main:create_app --factory
"""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import Settings, get_settings
from src.domain.repositories import UserRepository
from src.infrastructure.database.postgres import create_db_engine, create_session_factory
from src.interface.handlers.fastapi import dependencies as deps
from src.interface.handlers.fastapi.errors import register_exception_handlers
from src.interface.handlers.fastapi.routers import auth_router, health_router, users_router
from src.interface.repositories.postgres import PostgresUserRepository
from src.shared.security import BcryptPasswordHasher, JwtTokenService
from src.usecases import GetCurrentUser, LoginUser, RegisterUser
from src.usecases.ports import PasswordHasher, TokenService

# --- Per-request providers -------------------------------------------------------
# Module-level (not closures) so tests can target them with app.dependency_overrides.


def get_session(request: Request) -> Iterator[Session]:
    """One session, i.e. one transaction, per request: commit on success, roll back on error."""
    session_factory: sessionmaker[Session] = request.app.state.session_factory
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# scope="function" commits before the response is sent. With the default scope the
# client could already have its 201 while the commit is still pending or failing.
SessionDep = Annotated[Session, Depends(get_session, scope="function")]


def get_password_hasher(request: Request) -> PasswordHasher:
    return request.app.state.password_hasher


def get_token_service(request: Request) -> TokenService:
    return request.app.state.token_service


def get_user_repository(session: SessionDep) -> UserRepository:
    return PostgresUserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]
PasswordHasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
TokenServiceDep = Annotated[TokenService, Depends(get_token_service)]


def build_register_user(users: UserRepositoryDep, hasher: PasswordHasherDep) -> RegisterUser:
    return RegisterUser(users, hasher)


def build_login_user(
    users: UserRepositoryDep, hasher: PasswordHasherDep, tokens: TokenServiceDep
) -> LoginUser:
    return LoginUser(users, hasher, tokens)


def build_get_current_user(users: UserRepositoryDep) -> GetCurrentUser:
    return GetCurrentUser(users)


# --- Application factory ---------------------------------------------------------


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    # Process-wide singletons: created once here, shared by every request.
    engine = create_db_engine(str(settings.database_url))

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        engine.dispose()

    app = FastAPI(title="Python Clean Architecture API", version="0.1.0", lifespan=lifespan)

    app.state.session_factory = create_session_factory(engine)
    app.state.password_hasher = BcryptPasswordHasher()
    app.state.token_service = JwtTokenService(
        secret=settings.jwt_secret.get_secret_value(),
        expire_minutes=settings.jwt_expire_minutes,
        algorithm=settings.jwt_algorithm,
    )

    # Bind the contracts declared by the HTTP layer to concrete implementations.
    app.dependency_overrides.update(
        {
            deps.provide_register_user: build_register_user,
            deps.provide_login_user: build_login_user,
            deps.provide_get_current_user: build_get_current_user,
            deps.provide_token_service: get_token_service,
        }
    )

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    return app
