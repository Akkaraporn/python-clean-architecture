import pytest

from src.domain.entities import User
from src.domain.errors import InactiveUserError, InvalidCredentialsError
from src.usecases import LoginUser
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUserRepository
from tests.unit.usecases.conftest import PASSWORD


@pytest.fixture
def login(
    repository: FakeUserRepository, hasher: FakePasswordHasher, tokens: FakeTokenService
) -> LoginUser:
    return LoginUser(repository, hasher, tokens)


def test_returns_a_token_for_the_user(
    login: LoginUser, tokens: FakeTokenService, existing_user: User
) -> None:
    token = login.execute(email="jane@example.com", password=PASSWORD)

    assert tokens.decode(token) == existing_user.id


def test_email_lookup_is_case_insensitive(
    login: LoginUser, tokens: FakeTokenService, existing_user: User
) -> None:
    token = login.execute(email="  JANE@Example.com", password=PASSWORD)

    assert tokens.decode(token) == existing_user.id


def test_wrong_password_is_rejected(login: LoginUser, existing_user: User) -> None:
    with pytest.raises(InvalidCredentialsError):
        login.execute(email="jane@example.com", password="wrong-password")


def test_unknown_email_is_rejected(login: LoginUser) -> None:
    with pytest.raises(InvalidCredentialsError):
        login.execute(email="nobody@example.com", password=PASSWORD)


def test_unknown_email_and_wrong_password_are_indistinguishable(
    login: LoginUser, existing_user: User
) -> None:
    with pytest.raises(InvalidCredentialsError) as unknown:
        login.execute(email="nobody@example.com", password=PASSWORD)
    with pytest.raises(InvalidCredentialsError) as wrong:
        login.execute(email="jane@example.com", password="wrong-password")

    assert type(unknown.value) is type(wrong.value)
    assert str(unknown.value) == str(wrong.value)


def test_unknown_email_still_runs_password_verification(
    login: LoginUser, hasher: FakePasswordHasher
) -> None:
    # Skipping the slow hash check would make "no such user" measurably faster.
    with pytest.raises(InvalidCredentialsError):
        login.execute(email="nobody@example.com", password=PASSWORD)

    assert hasher.verify_calls == 1


def test_deactivated_user_cannot_log_in(login: LoginUser, inactive_user: User) -> None:
    with pytest.raises(InactiveUserError):
        login.execute(email=inactive_user.email, password=PASSWORD)


def test_deactivated_user_with_wrong_password_gets_the_generic_error(
    login: LoginUser, inactive_user: User
) -> None:
    # Account status is only revealed to someone who already knows the password.
    with pytest.raises(InvalidCredentialsError):
        login.execute(email=inactive_user.email, password="wrong-password")
