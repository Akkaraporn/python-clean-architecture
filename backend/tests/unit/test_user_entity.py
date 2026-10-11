from dataclasses import replace
from datetime import UTC
from uuid import UUID, uuid4

import pytest

from src.domain.entities import User, normalize_email
from src.domain.errors import (
    DomainError,
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.repositories import UserRepository


def make_user(**overrides: object) -> User:
    defaults: dict[str, object] = {
        "email": "jane@example.com",
        "hashed_password": "hashed-secret",
        "full_name": "Jane Doe",
    }
    return User.create(**{**defaults, **overrides})  # type: ignore[arg-type]


def test_create_assigns_identity_and_defaults() -> None:
    user = make_user()

    assert isinstance(user.id, UUID)
    assert user.is_active is True
    assert user.created_at.tzinfo is UTC


def test_create_generates_a_new_id_each_time() -> None:
    assert make_user().id != make_user().id


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Jane@Example.COM", "jane@example.com"),
        ("  jane@example.com \n", "jane@example.com"),
        ("jane@example.com", "jane@example.com"),
    ],
)
def test_email_is_normalized(raw: str, expected: str) -> None:
    assert normalize_email(raw) == expected
    assert make_user(email=raw).email == expected


def test_email_is_normalized_when_rebuilt_from_storage() -> None:
    user = User(id=uuid4(), email="JANE@example.com", hashed_password="h", full_name="Jane")

    assert user.email == "jane@example.com"


def test_full_name_is_trimmed() -> None:
    assert make_user(full_name="  Jane Doe  ").full_name == "Jane Doe"


def test_deactivate_and_activate() -> None:
    user = make_user()

    user.deactivate()
    assert user.is_active is False

    user.activate()
    assert user.is_active is True


def test_equality_is_based_on_identity() -> None:
    user = make_user()
    renamed = replace(user, full_name="Someone Else")

    assert user == renamed
    assert hash(user) == hash(renamed)
    assert user != make_user()
    assert user != "not a user"


def test_password_hash_is_hidden_from_repr() -> None:
    assert "hashed-secret" not in repr(make_user())


def test_repository_contract_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        UserRepository()  # type: ignore[abstract]


def test_repository_implementation_must_define_every_method() -> None:
    class Incomplete(UserRepository):
        def add(self, user: User) -> User:
            return user

    with pytest.raises(TypeError, match="get_by_email|get_by_id"):
        Incomplete()  # type: ignore[abstract]


@pytest.mark.parametrize(
    "error",
    [
        UserAlreadyExistsError("jane@example.com"),
        InvalidCredentialsError(),
        InactiveUserError(),
        UserNotFoundError(uuid4()),
    ],
)
def test_domain_errors_share_a_base_class(error: DomainError) -> None:
    assert isinstance(error, DomainError)


def test_invalid_credentials_message_does_not_reveal_which_part_failed() -> None:
    assert str(InvalidCredentialsError()) == "Invalid email or password"
