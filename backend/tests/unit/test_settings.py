from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.config.settings import Settings, get_settings

VALID_SECRET = "x" * 32
VALID_DB_URL = "postgresql+psycopg://user:pass@localhost:5433/app"
SETTING_VARS = (
    "DATABASE_URL",
    "JWT_SECRET",
    "JWT_ALGORITHM",
    "JWT_EXPIRE_MINUTES",
    "CORS_ORIGINS",
    "LOG_LEVEL",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Keep the developer's shell and .env from leaking into the assertions.
    for name in SETTING_VARS:
        monkeypatch.delenv(name, raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", VALID_DB_URL)
    monkeypatch.setenv("JWT_SECRET", VALID_SECRET)


def load() -> Settings:
    return Settings(_env_file=None)  # type: ignore[call-arg]


def test_reads_and_converts_values_from_environment(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JWT_ALGORITHM", "HS512")
    monkeypatch.setenv("JWT_SECRET", "y" * 64)
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "45")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173, http://example.com")

    settings = load()

    assert str(settings.database_url) == VALID_DB_URL
    assert settings.jwt_secret.get_secret_value() == "y" * 64
    assert settings.jwt_algorithm == "HS512"
    assert settings.jwt_expire_minutes == 45
    assert settings.cors_origins == ["http://localhost:5173", "http://example.com"]


def test_optional_values_have_defaults(required_env: None) -> None:
    settings = load()

    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expire_minutes == 30
    assert settings.cors_origins == []
    assert settings.log_level == "INFO"


def test_reads_values_from_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={VALID_DB_URL}\nJWT_SECRET={VALID_SECRET}\nPOSTGRES_USER=ignored\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert str(settings.database_url) == VALID_DB_URL


def test_environment_overrides_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_URL={VALID_DB_URL}\nJWT_SECRET={VALID_SECRET}\nJWT_EXPIRE_MINUTES=10\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "20")

    settings = Settings(_env_file=env_file)  # type: ignore[call-arg]

    assert settings.jwt_expire_minutes == 20


@pytest.mark.parametrize("missing", ["DATABASE_URL", "JWT_SECRET"])
def test_missing_required_value_fails_fast(
    required_env: None, monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    monkeypatch.delenv(missing)

    with pytest.raises(ValidationError) as exc_info:
        load()

    assert exc_info.value.errors()[0]["type"] == "missing"
    assert exc_info.value.errors()[0]["loc"] == (missing.lower(),)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("JWT_EXPIRE_MINUTES", "thirty"),
        ("JWT_EXPIRE_MINUTES", "0"),
        ("JWT_EXPIRE_MINUTES", "-5"),
        ("JWT_ALGORITHM", "none"),
        ("JWT_ALGORITHM", "RS256"),
        ("JWT_SECRET", "too-short"),
        ("DATABASE_URL", "not-a-url"),
        ("DATABASE_URL", "mysql://user:pass@localhost/app"),
    ],
)
def test_invalid_value_is_rejected(
    required_env: None, monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        load()


@pytest.mark.parametrize(("algorithm", "min_length"), [("HS384", 48), ("HS512", 64)])
def test_stronger_algorithm_requires_longer_secret(
    required_env: None, monkeypatch: pytest.MonkeyPatch, algorithm: str, min_length: int
) -> None:
    monkeypatch.setenv("JWT_ALGORITHM", algorithm)

    monkeypatch.setenv("JWT_SECRET", "z" * (min_length - 1))
    with pytest.raises(ValidationError, match=f"at least {min_length}"):
        load()

    monkeypatch.setenv("JWT_SECRET", "z" * min_length)
    assert load().jwt_algorithm == algorithm


def test_secret_is_hidden_from_repr(required_env: None) -> None:
    settings = load()

    assert VALID_SECRET not in repr(settings)
    assert VALID_SECRET not in str(settings.model_dump())


def test_get_settings_is_cached(required_env: None) -> None:
    assert get_settings() is get_settings()


def test_cors_origins_drop_trailing_slash(
    required_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:5173/,https://app.example.com")

    assert load().cors_origins == ["http://localhost:5173", "https://app.example.com"]


@pytest.mark.parametrize("value", ["*", "http://ok.example.com,*", "localhost:5173"])
def test_cors_origins_must_be_explicit_urls(
    required_env: None, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv("CORS_ORIGINS", value)

    with pytest.raises(ValidationError):
        load()


def test_log_level_is_case_insensitive(required_env: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")

    assert load().log_level == "DEBUG"
