from functools import lru_cache

from src.domain.entities import normalize_email
from src.domain.errors import InactiveUserError, InvalidCredentialsError
from src.domain.repositories import UserRepository
from src.usecases.ports import PasswordHasher, TokenService


@lru_cache(maxsize=8)
def _dummy_hash(hasher: PasswordHasher) -> str:
    # Built once per hasher so it uses the same algorithm and cost as real hashes.
    return hasher.hash("dummy-password-used-only-to-equalize-timing")


class LoginUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher, tokens: TokenService) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    def execute(self, *, email: str, password: str) -> str:
        user = self._users.get_by_email(normalize_email(email))

        if user is None:
            # Run a verify anyway so an unknown email takes as long as a wrong password,
            # otherwise response time reveals which emails are registered.
            self._hasher.verify(password, _dummy_hash(self._hasher))
            raise InvalidCredentialsError()

        if not self._hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError()

        # Only checked after the password, so account status is never disclosed
        # to someone who does not know the credentials.
        if not user.is_active:
            raise InactiveUserError()

        return self._tokens.create_access_token(user.id)
