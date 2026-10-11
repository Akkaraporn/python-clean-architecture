from datetime import UTC, datetime
from uuid import uuid4

from src.domain.entities import User
from src.infrastructure.database.postgres.models import UserModel
from src.interface.repositories.postgres.user_mapper import to_entity, to_model


def make_user() -> User:
    user = User(
        id=uuid4(),
        email="jane@example.com",
        hashed_password="hashed::pw",
        full_name="Jane Doe",
        created_at=datetime(2030, 1, 2, 3, 4, 5, tzinfo=UTC),
    )
    user.deactivate()
    return user


def test_to_model_copies_every_field() -> None:
    user = make_user()

    model = to_model(user)

    assert isinstance(model, UserModel)
    assert model.id == user.id
    assert model.email == user.email
    assert model.hashed_password == user.hashed_password
    assert model.full_name == user.full_name
    assert model.is_active is False
    assert model.created_at == user.created_at


def test_round_trip_preserves_every_field() -> None:
    user = make_user()

    restored = to_entity(to_model(user))

    assert type(restored) is User
    assert restored is not user
    assert vars_of(restored) == vars_of(user)


def vars_of(user: User) -> dict[str, object]:
    return {name: getattr(user, name) for name in User.__slots__}
