import pytest

from src.domain.entities import User
from src.domain.errors import UserAlreadyExistsError
from src.usecases import RegisterUser
from tests.fakes import FakePasswordHasher, FakeUserRepository


@pytest.fixture
def register(repository: FakeUserRepository, hasher: FakePasswordHasher) -> RegisterUser:
    return RegisterUser(repository, hasher)


def test_registers_a_new_user(register: RegisterUser, repository: FakeUserRepository) -> None:
    user = register.execute(email="new@example.com", password="s3cret-pass", full_name="New User")

    assert user.email == "new@example.com"
    assert user.full_name == "New User"
    assert user.is_active is True
    assert repository.get_by_id(user.id) == user


def test_stores_a_hash_not_the_plain_password(
    register: RegisterUser, repository: FakeUserRepository
) -> None:
    user = register.execute(email="new@example.com", password="s3cret-pass", full_name="New")

    stored = repository.get_by_id(user.id)
    assert stored is not None
    assert stored.hashed_password == "hashed::s3cret-pass"


def test_normalizes_email_before_saving(
    register: RegisterUser, repository: FakeUserRepository
) -> None:
    user = register.execute(email="  New@Example.COM ", password="s3cret-pass", full_name="New")

    assert user.email == "new@example.com"
    assert repository.get_by_email("new@example.com") is not None


@pytest.mark.parametrize("email", ["jane@example.com", "JANE@Example.com", " jane@example.com "])
def test_rejects_an_email_that_is_already_registered(
    register: RegisterUser, repository: FakeUserRepository, existing_user: User, email: str
) -> None:
    with pytest.raises(UserAlreadyExistsError):
        register.execute(email=email, password="another-pass", full_name="Impostor")

    assert len(repository) == 1


def test_skips_the_expensive_hash_when_email_is_taken(
    repository: FakeUserRepository, existing_user: User
) -> None:
    class ExplodingHasher(FakePasswordHasher):
        def hash(self, password: str) -> str:
            raise AssertionError("hash() should not run for a duplicate email")

    with pytest.raises(UserAlreadyExistsError):
        RegisterUser(repository, ExplodingHasher()).execute(
            email="jane@example.com", password="another-pass", full_name="Jane"
        )
