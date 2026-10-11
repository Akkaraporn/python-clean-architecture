from uuid import uuid4

import pytest

from src.domain.entities import User
from src.domain.errors import InactiveUserError, UserNotFoundError
from src.usecases import GetCurrentUser
from tests.fakes import FakeUserRepository


@pytest.fixture
def get_current_user(repository: FakeUserRepository) -> GetCurrentUser:
    return GetCurrentUser(repository)


def test_returns_the_user(get_current_user: GetCurrentUser, existing_user: User) -> None:
    user = get_current_user.execute(existing_user.id)

    assert user == existing_user
    assert user.email == "jane@example.com"


def test_unknown_id_raises_not_found(get_current_user: GetCurrentUser) -> None:
    missing_id = uuid4()

    with pytest.raises(UserNotFoundError) as exc_info:
        get_current_user.execute(missing_id)

    assert exc_info.value.user_id == missing_id


def test_deactivated_user_is_rejected(
    get_current_user: GetCurrentUser, inactive_user: User
) -> None:
    # Stops tokens that are still within their lifetime from working once an account is disabled.
    with pytest.raises(InactiveUserError):
        get_current_user.execute(inactive_user.id)
