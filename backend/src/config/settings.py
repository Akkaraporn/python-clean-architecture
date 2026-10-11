from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# Local runs start from backend/, but the single .env lives at the repo root next to
# docker-compose.yml. A missing file is ignored, so containers rely on real env vars.
REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

# An HMAC key should be at least as long as the hash output (RFC 7518 section 3.2).
MIN_SECRET_LENGTH = {"HS256": 32, "HS384": 48, "HS512": 64}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        # The shared .env also carries POSTGRES_* for docker compose.
        extra="ignore",
    )

    database_url: PostgresDsn

    jwt_secret: SecretStr = Field(min_length=MIN_SECRET_LENGTH["HS256"])
    # Whitelisting HMAC algorithms rules out "none" and asymmetric algorithms
    # that would need a different key setup.
    jwt_algorithm: Literal["HS256", "HS384", "HS512"] = "HS256"
    jwt_expire_minutes: int = Field(default=30, gt=0, le=1440)

    # NoDecode lets us accept a plain comma-separated value instead of a JSON array.
    cors_origins: Annotated[list[str], NoDecode] = []

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @model_validator(mode="after")
    def secret_is_long_enough_for_algorithm(self) -> Self:
        required = MIN_SECRET_LENGTH[self.jwt_algorithm]
        if len(self.jwt_secret.get_secret_value()) < required:
            raise ValueError(
                f"JWT_SECRET must be at least {required} characters for {self.jwt_algorithm}"
            )
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_comma_separated(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def origins_are_explicit(cls, origins: list[str]) -> list[str]:
        normalized = []
        for origin in origins:
            if origin == "*":
                raise ValueError("list allowed origins explicitly instead of '*'")
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"origin must start with http:// or https://: {origin!r}")
            # Browsers send the Origin header without a trailing slash, so
            # "http://localhost:5173/" would never match.
            normalized.append(origin.rstrip("/"))
        return normalized

    @field_validator("log_level", mode="before")
    @classmethod
    def upper_case_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # required fields come from the environment
