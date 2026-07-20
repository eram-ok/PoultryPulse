from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """PoultryPulse application configuration."""

    app_name: str = "PoultryPulse"
    app_version: str = "0.1.0"
    app_environment: str = "development"
    app_debug: bool = True

    api_v1_prefix: str = "/api/v1"

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "poultrypulse"
    database_user: str
    database_password: str
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings object."""

    return Settings()
