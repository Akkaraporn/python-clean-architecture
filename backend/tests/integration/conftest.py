"""PostgreSQL fixtures for integration tests.

Tests run against a dedicated `<db>_test` database (or TEST_DATABASE_URL) that is
created and migrated with Alembic on first use. Each test runs inside a transaction
that is rolled back afterwards, so tests never see each other's data.
"""

import os
from argparse import Namespace
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import URL, Engine, create_engine, make_url, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from src.infrastructure.database.postgres import create_db_engine

MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[2] / "src/infrastructure/database/postgres/migrations"
)


def _test_database_url() -> URL:
    if override := os.environ.get("TEST_DATABASE_URL"):
        return make_url(override)
    from src.config.settings import get_settings

    app_url = make_url(str(get_settings().database_url))
    return app_url.set(database=f"{app_url.database}_test")


def _create_database_if_missing(url: URL) -> None:
    # The timeout turns "Docker is not running" into a quick skip instead of a long hang.
    admin_engine = create_engine(url.set(database="postgres"), connect_args={"connect_timeout": 3})
    try:
        # CREATE DATABASE cannot run inside a transaction block.
        with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    finally:
        admin_engine.dispose()


def _migrate(url: URL) -> None:
    # Built in code rather than from alembic.ini so Alembic does not reconfigure
    # logging for the whole test session.
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.cmd_opts = Namespace(x=[f"database_url={url.render_as_string(hide_password=False)}"])
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    url = _test_database_url()
    try:
        _create_database_if_missing(url)
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is not reachable ({exc.orig}); run: docker compose up -d db")
    _migrate(url)

    engine = create_db_engine(url.render_as_string(hide_password=False))
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    connection = db_engine.connect()
    outer = connection.begin()
    # Commits or rollbacks made by code under test only touch savepoints;
    # the outer transaction is always rolled back below.
    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()
