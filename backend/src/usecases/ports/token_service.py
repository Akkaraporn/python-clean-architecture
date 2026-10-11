from abc import ABC, abstractmethod
from uuid import UUID


class TokenService(ABC):
    """Issues and validates access tokens that identify a user."""

    @abstractmethod
    def create_access_token(self, user_id: UUID) -> str:
        """Return a signed access token for the user."""

    @abstractmethod
    def decode(self, token: str) -> UUID:
        """Return the user id carried by a valid token.

        Raises:
            ExpiredTokenError: if the token is past its expiry time.
            InvalidTokenError: for any other problem (bad signature, malformed, ...).
        """
