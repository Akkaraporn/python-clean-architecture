from src.domain.entities import User
from src.infrastructure.database.postgres.models import UserModel


def to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        hashed_password=model.hashed_password,
        full_name=model.full_name,
        is_active=model.is_active,
        created_at=model.created_at,
    )


def to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email,
        hashed_password=user.hashed_password,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
