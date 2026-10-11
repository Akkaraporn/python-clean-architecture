"""In-memory test doubles that honour the same contracts as the real adapters."""

from dataclasses import replace
from uuid import UUID

from src.domain.entities import User
from src.domain.errors import InvalidTokenError, UserAlreadyExistsError
from src.domain.repositories import UserRepository
from src.usecases.ports import PasswordHasher, TokenService


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._users: dict[UUID, User] = {}

    # Copies mimic a database: callers cannot change stored state by mutating a result.
    def add(self, user: User) -> User:
        if any(existing.email == user.email for existing in self._users.values()):
            raise UserAlreadyExistsError(user.email)
        self._users[user.id] = replace(user)
        return replace(user)

    def get_by_id(self, user_id: UUID) -> User | None:
        user = self._users.get(user_id)
        return replace(user) if user else None

    def get_by_email(self, email: str) -> User | None:
        user = next((u for u in self._users.values() if u.email == email), None)
        return replace(user) if user else None

    def __len__(self) -> int:
        return len(self._users)


class FakePasswordHasher(PasswordHasher):
    PREFIX = "hashed::"

    def __init__(self) -> None:
        self.verify_calls = 0

    def hash(self, password: str) -> str:
        return f"{self.PREFIX}{password}"

    def verify(self, password: str, hashed_password: str) -> bool:
        self.verify_calls += 1
        return hashed_password == f"{self.PREFIX}{password}"


class FakeTokenService(TokenService):
    PREFIX = "token-for-"

    def create_access_token(self, user_id: UUID) -> str:
        return f"{self.PREFIX}{user_id}"

    def decode(self, token: str) -> UUID:
        if not token.startswith(self.PREFIX):
            raise InvalidTokenError()
        return UUID(token.removeprefix(self.PREFIX))
