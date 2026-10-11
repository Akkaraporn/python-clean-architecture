import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine, inspect

from src.infrastructure.database.postgres.base import Base
from src.infrastructure.database.postgres.models import UserModel  # noqa: F401
from tests.conftest import alembic_config

pytestmark = pytest.mark.integration


def test_models_match_the_migrated_schema(db_engine: Engine) -> None:
    # Equivalent to `alembic check`: a model change without a migration fails here.
    with db_engine.connect() as connection:
        diff = compare_metadata(
            MigrationContext.configure(connection, opts={"compare_type": True}), Base.metadata
        )

    assert diff == []


def test_downgrade_and_upgrade_round_trip(db_engine: Engine) -> None:
    config = alembic_config(db_engine.url)
    try:
        command.downgrade(config, "base")
        assert "users" not in inspect(db_engine).get_table_names()
    finally:
        # Always restore head so the remaining tests see the full schema.
        command.upgrade(config, "head")

    assert "users" in inspect(db_engine).get_table_names()
