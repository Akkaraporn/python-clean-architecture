"""HTTP endpoints. Each handler only converts the request, calls one use case and
converts the result; business rules live in the use cases."""

from fastapi import APIRouter, status

from src.interface.handlers.fastapi.dependencies import (
    CurrentUserId,
    GetCurrentUserDep,
    LoginUserDep,
    RegisterUserDep,
)
from src.interface.handlers.fastapi.schemas import (
    ErrorResponse,
    HealthResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

auth_router = APIRouter(prefix="/api/auth", tags=["auth"])
users_router = APIRouter(prefix="/api/users", tags=["users"])
health_router = APIRouter(tags=["health"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
    summary="Create a new account",
)
def register(body: RegisterRequest, register_user: RegisterUserDep) -> UserResponse:
    user = register_user.execute(email=body.email, password=body.password, full_name=body.full_name)
    return UserResponse.model_validate(user)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
    summary="Exchange email and password for an access token",
)
def login(body: LoginRequest, login_user: LoginUserDep) -> TokenResponse:
    token = login_user.execute(email=body.email, password=body.password)
    return TokenResponse(access_token=token)


@users_router.get(
    "/me",
    response_model=UserResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    },
    summary="Return the account that owns the access token",
)
def read_me(user_id: CurrentUserId, get_current_user: GetCurrentUserDep) -> UserResponse:
    return UserResponse.model_validate(get_current_user.execute(user_id))


@health_router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health() -> HealthResponse:
    return HealthResponse()
