from src.domain.entities import User, normalize_email
from src.domain.errors import UserAlreadyExistsError
from src.domain.repositories import UserRepository
from src.usecases.ports import PasswordHasher


class RegisterUser:
    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self._users = users
        self._hasher = hasher

    def execute(self, *, email: str, password: str, full_name: str) -> User:
        email = normalize_email(email)

        # Checked before hashing to give a clear error without paying for the slow hash.
        # The repository still raises on a concurrent duplicate (unique index).
        if self._users.get_by_email(email) is not None:
            raise UserAlreadyExistsError(email)

        user = User.create(
            email=email,
            hashed_password=self._hasher.hash(password),
            full_name=full_name,
        )
        return self._users.add(user)
