import inspect

import pytest

from src.config.settings import Settings
from src.infrastructure.fastapi.main import create_app
from src.interface.handlers.fastapi import dependencies

PROVIDERS = [
    function
    for name, function in inspect.getmembers(dependencies, inspect.isfunction)
    if name.startswith("provide_")
]


@pytest.fixture
def settings() -> Settings:
    # create_engine is lazy, so no database is contacted here.
    return Settings(  # type: ignore[call-arg]
        _env_file=None,
        database_url="postgresql+psycopg://user:pass@localhost:5432/unused",
        jwt_secret="x" * 32,
    )


@pytest.mark.parametrize("provider", PROVIDERS, ids=lambda f: f.__name__)
def test_unwired_provider_fails_loudly(provider: object) -> None:
    with pytest.raises(NotImplementedError, match="composition root"):
        provider()  # type: ignore[operator]


@pytest.mark.parametrize("provider", PROVIDERS, ids=lambda f: f.__name__)
def test_composition_root_binds_every_provider(settings: Settings, provider: object) -> None:
    # A new provide_* contract that main.py forgets to bind would only fail at request time.
    assert provider in create_app(settings).dependency_overrides
