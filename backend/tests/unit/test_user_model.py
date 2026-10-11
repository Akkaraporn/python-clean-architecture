from sqlalchemy import Index

from src.infrastructure.database.postgres.base import Base
from src.infrastructure.database.postgres.models import UserModel


def test_users_table_is_registered_on_the_shared_metadata() -> None:
    assert Base.metadata.tables["users"] is UserModel.__table__


def test_every_column_is_required() -> None:
    nullable = [column.name for column in UserModel.__table__.columns if column.nullable]

    assert nullable == []


def test_email_has_a_unique_index() -> None:
    indexes: set[Index] = UserModel.__table__.indexes
    email_index = next(index for index in indexes if index.name == "ix_users_email")

    assert email_index.unique
    assert [column.name for column in email_index.columns] == ["email"]


def test_id_has_no_database_default() -> None:
    # The domain generates ids; a server default would hide a missing id bug.
    id_column = UserModel.__table__.columns["id"]

    assert id_column.primary_key
    assert id_column.server_default is None
    assert id_column.default is None
