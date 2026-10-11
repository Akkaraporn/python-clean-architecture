from abc import ABC, abstractmethod


class PasswordHasher(ABC):
    """One-way password hashing, so use cases never depend on a specific algorithm."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a salted hash of the plain-text password."""

    @abstractmethod
    def verify(self, password: str, hashed_password: str) -> bool:
        """Return True if the password matches the hash; never raises for bad input."""
