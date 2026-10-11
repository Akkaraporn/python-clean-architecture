from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from src.config.settings import get_settings
from src.infrastructure.database.postgres.base import Base

# Importing the models registers their tables on Base.metadata for autogenerate.
from src.infrastructure.database.postgres.models import UserModel  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url() -> str:
    # `alembic -x database_url=...` targets another database (e.g. the test DB)
    # without editing .env.
    override = context.get_x_argument(as_dictionary=True).get("database_url")
    return override or str(get_settings().database_url)


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of executing it (`alembic upgrade head --sql`)."""
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # NullPool: a migration run is a one-off process, so pooling connections is pointless.
    connectable = create_engine(get_database_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
