"""Environment-only configuration. Never serialize settings or raw validation errors."""
from functools import lru_cache
from typing import Literal, TypeVar
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class ConfigurationError(RuntimeError):
    """Safe to display: contains variable names, never their values."""


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True, extra="ignore", hide_input_in_errors=True,
        env_file=None, frozen=True,
    )


class DatabaseSettings(EnvironmentSettings):
    DATABASE_URL: SecretStr

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url(cls, value: SecretStr) -> SecretStr:
        try:
            url = make_url(value.get_secret_value())
            valid = (
                url.drivername == "postgresql+psycopg" and url.host
                and url.username and url.username.startswith("postgres.")
                and url.password and url.database and url.port == 5432
            )
        except Exception:
            valid = False
        if not valid:
            raise ValueError("requires a PostgreSQL Session pooler URL")
        return value


class CorsSettings(EnvironmentSettings):
    FRONTEND_ORIGIN: str = Field(min_length=1)

    @field_validator("FRONTEND_ORIGIN")
    @classmethod
    def single_origin(cls, value: str) -> str:
        try:
            parsed = urlsplit(value)
            valid = (
                parsed.scheme in {"http", "https"} and parsed.hostname
                and not parsed.username and not parsed.password
                and parsed.path in {"", "/"} and not parsed.query
                and not parsed.fragment and "*" not in value
            )
            _ = parsed.port
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("requires one HTTP origin")
        return value.rstrip("/")


class Settings(DatabaseSettings, CorsSettings):
    ENV: Literal["local", "production"]
    SUPABASE_URL: SecretStr = Field(min_length=1)
    SUPABASE_SERVICE_ROLE_KEY: SecretStr = Field(min_length=1)
    STORAGE_BUCKET: str = Field(min_length=1)
    GEMINI_API_KEY: SecretStr = Field(min_length=1)
    GEMINI_MODEL: str = Field(min_length=1)
    JWT_SECRET: SecretStr = Field(min_length=1)
    ACCESS_TOKEN_MINUTES: int = Field(gt=0)
    PENDING_TOKEN_MINUTES: int = Field(gt=0)
    FERNET_KEY: SecretStr = Field(min_length=1)
    # Required only for seeding, not for serving health or running migrations.
    SEED_PASSWORD: SecretStr | None = None

    @field_validator("GEMINI_MODEL")
    @classmethod
    def pinned_model(cls, value: str) -> str:
        if "latest" in value.lower():
            raise ValueError("requires a pinned model")
        return value


class SeedSettings(DatabaseSettings):
    SEED_PASSWORD: SecretStr = Field(min_length=8)

    @field_validator("SEED_PASSWORD")
    @classmethod
    def bcrypt_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) > 72:
            raise ValueError("exceeds bcrypt byte limit")
        return value


T = TypeVar("T", bound=EnvironmentSettings)


def load_settings(kind: type[T]) -> T:
    try:
        return kind()
    except ValidationError as exc:
        # Do not chain the original error: errors() includes unredacted input.
        names = sorted({str(error["loc"][0]) for error in exc.errors()})
        raise ConfigurationError(
            "Missing or invalid environment variables: " + ", ".join(names)
        ) from None


@lru_cache
def get_settings() -> Settings:
    return load_settings(Settings)
