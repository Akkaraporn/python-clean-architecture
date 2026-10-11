from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Local runs start from backend/, but the single .env lives at the repo root next to
# docker-compose.yml. A missing file is ignored, so containers rely on real env vars.
REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        # The shared .env also carries POSTGRES_* for docker compose.
        extra="ignore",
    )

    database_url: PostgresDsn

    # HS256 needs a key of at least 256 bits (RFC 7518 section 3.2).
    jwt_secret: SecretStr = Field(min_length=32)
    # Whitelisting HMAC algorithms rules out "none" and asymmetric algorithms
    # that would need a different key setup.
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_expire_minutes: int = Field(default=30, gt=0, le=1440)

    # NoDecode lets us accept a plain comma-separated value instead of a JSON array.
    cors_origins: Annotated[list[str], NoDecode] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
