import pytest

from src.domain.entities import User
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUserRepository

PASSWORD = "correct-horse-battery"


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def tokens() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def existing_user(repository: FakeUserRepository, hasher: FakePasswordHasher) -> User:
    return repository.add(
        User.create(
            email="jane@example.com", hashed_password=hasher.hash(PASSWORD), full_name="Jane Doe"
        )
    )


@pytest.fixture
def inactive_user(repository: FakeUserRepository, hasher: FakePasswordHasher) -> User:
    user = User.create(
        email="gone@example.com", hashed_password=hasher.hash(PASSWORD), full_name="Gone"
    )
    user.deactivate()
    return repository.add(user)
