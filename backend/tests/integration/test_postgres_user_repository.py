"""PostgreSQL-specific behaviour that the in-memory fake has no equivalent for."""

import pytest
from sqlalchemy import Engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.domain.entities import User
from src.infrastructure.database.postgres.models import UserModel
from src.interface.repositories.postgres import PostgresUserRepository

pytestmark = pytest.mark.integration


@pytest.fixture
def repository(db_session: Session) -> PostgresUserRepository:
    return PostgresUserRepository(db_session)


def make_user(email: str = "jane@example.com") -> User:
    return User.create(email=email, hashed_password="hashed::pw", full_name="Jane Doe")


def test_add_does_not_commit(
    repository: PostgresUserRepository, db_session: Session, db_engine: Engine
) -> None:
    user = repository.add(make_user())
    assert repository.get_by_id(user.id) is not None

    # A separate connection cannot see the row: committing is the caller's job.
    with db_engine.connect() as other_connection:
        visible = other_connection.scalar(
            select(func.count()).select_from(UserModel).where(UserModel.id == user.id)
        )
    assert visible == 0

    db_session.rollback()
    assert repository.get_by_id(user.id) is None


def test_get_returns_a_domain_entity_not_the_orm_model(
    repository: PostgresUserRepository,
) -> None:
    user = repository.add(make_user())

    found = repository.get_by_id(user.id)

    assert type(found) is User
    assert not isinstance(found, UserModel)


def test_created_at_keeps_its_timezone(repository: PostgresUserRepository) -> None:
    user = repository.add(make_user())

    found = repository.get_by_id(user.id)

    assert found is not None
    assert found.created_at == user.created_at
    assert found.created_at.utcoffset() is not None


def test_other_integrity_errors_are_not_reported_as_duplicate_email(
    repository: PostgresUserRepository,
) -> None:
    # Same id, different email: a primary-key clash is a bug, not a business rule,
    # so it must surface as-is instead of being disguised as UserAlreadyExistsError.
    original = repository.add(make_user())
    clash = User(
        id=original.id,
        email="someone-else@example.com",
        hashed_password="h",
        full_name="Other",
    )

    with pytest.raises(IntegrityError):
        repository.add(clash)
