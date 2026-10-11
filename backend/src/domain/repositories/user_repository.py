from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities.user import User


class UserRepository(ABC):
    """Persistence port for users.

    Declared in the domain so use cases depend on this contract, while the
    storage technology (PostgreSQL, in-memory, ...) is plugged in from outside.
    """

    @abstractmethod
    def add(self, user: User) -> User:
        """Persist a new user.

        Raises:
            UserAlreadyExistsError: if another user already has the same email.
        """

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        """Return the user with this id, or None if there is none."""

    @abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Return the user with this (already normalized) email, or None."""
