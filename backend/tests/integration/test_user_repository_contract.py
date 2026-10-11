"""One behaviour spec, two implementations.

Passing against both the in-memory fake and PostgreSQL shows the fake used by the
use-case unit tests behaves like the real thing.
"""

from dataclasses import replace
from uuid import uuid4

import pytest

from src.domain.entities import User
from src.domain.errors import UserAlreadyExistsError
from src.domain.repositories import UserRepository
from src.interface.repositories.postgres import PostgresUserRepository
from tests.fakes import FakeUserRepository


@pytest.fixture(
    params=["fake", pytest.param("postgres", marks=pytest.mark.integration)],
)
def repository(request: pytest.FixtureRequest) -> UserRepository:
    if request.param == "fake":
        return FakeUserRepository()
    return PostgresUserRepository(request.getfixturevalue("db_session"))


def make_user(email: str = "jane@example.com") -> User:
    return User.create(email=email, hashed_password="hashed::pw", full_name="Jane Doe")


def assert_same_state(actual: User | None, expected: User) -> None:
    # Entities compare by id only, so check every field explicitly.
    assert actual is not None
    assert isinstance(actual, User)
    assert (
        actual.id,
        actual.email,
        actual.hashed_password,
        actual.full_name,
        actual.is_active,
        actual.created_at,
    ) == (
        expected.id,
        expected.email,
        expected.hashed_password,
        expected.full_name,
        expected.is_active,
        expected.created_at,
    )


def test_add_returns_the_stored_user(repository: UserRepository) -> None:
    user = make_user()

    assert_same_state(repository.add(user), user)


def test_added_user_can_be_found_by_id(repository: UserRepository) -> None:
    user = make_user()
    repository.add(user)

    assert_same_state(repository.get_by_id(user.id), user)


def test_added_user_can_be_found_by_email(repository: UserRepository) -> None:
    user = make_user()
    repository.add(user)

    assert_same_state(repository.get_by_email("jane@example.com"), user)


def test_inactive_flag_is_persisted(repository: UserRepository) -> None:
    user = make_user()
    user.deactivate()
    repository.add(user)

    found = repository.get_by_id(user.id)
    assert found is not None
    assert found.is_active is False


def test_unknown_id_returns_none(repository: UserRepository) -> None:
    assert repository.get_by_id(uuid4()) is None


def test_unknown_email_returns_none(repository: UserRepository) -> None:
    repository.add(make_user())

    assert repository.get_by_email("nobody@example.com") is None


def test_duplicate_email_raises_domain_error(repository: UserRepository) -> None:
    repository.add(make_user())

    with pytest.raises(UserAlreadyExistsError) as exc_info:
        repository.add(make_user())

    assert exc_info.value.email == "jane@example.com"


def test_repository_stays_usable_after_a_duplicate(repository: UserRepository) -> None:
    first = repository.add(make_user())
    with pytest.raises(UserAlreadyExistsError):
        repository.add(make_user())

    second = repository.add(make_user("john@example.com"))

    assert repository.get_by_id(first.id) is not None
    assert repository.get_by_id(second.id) is not None


def test_mutating_a_returned_user_does_not_change_storage(repository: UserRepository) -> None:
    user = make_user()
    repository.add(user)

    found = repository.get_by_id(user.id)
    assert found is not None
    found.deactivate()
    renamed = replace(found, full_name="Changed")

    stored = repository.get_by_id(user.id)
    assert stored is not None
    assert stored.is_active is True
    assert stored.full_name == "Jane Doe"
    assert renamed.full_name == "Changed"
