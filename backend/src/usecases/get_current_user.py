from uuid import UUID

from src.domain.entities import User
from src.domain.errors import InactiveUserError, UserNotFoundError
from src.domain.repositories import UserRepository


class GetCurrentUser:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def execute(self, user_id: UUID) -> User:
        user = self._users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        # A token outlives a deactivation, so the account is re-checked on every request.
        if not user.is_active:
            raise InactiveUserError()
        return user
