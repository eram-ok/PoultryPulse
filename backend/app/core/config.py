from __future__ import annotations

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


PRODUCTION_ENVIRONMENTS = {
    "production",
    "prod",
}

ALLOWED_JWT_ALGORITHMS = {
    "HS256",
    "HS384",
    "HS512",
}

INSECURE_SECRET_VALUES = {
    "change-me",
    "changeme",
    "development",
    "password",
    "secret",
    "your-secret-key",
}


class Settings(BaseSettings):
    """PoultryPulse application configuration."""

    app_name: str = "PoultryPulse"
    app_version: str = "0.1.0"
    app_environment: str = "development"
    app_debug: bool = True

    api_v1_prefix: str = "/api/v1"
    docs_enabled: bool = True

    database_host: str = "localhost"
    database_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
    )
    database_name: str = "poultrypulse"
    database_user: str
    database_password: str
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "PoultryPulse"
    jwt_audience: str = "poultrypulse-api"
    jwt_validate_issuer_audience: bool = False
    jwt_leeway_seconds: int = Field(
        default=30,
        ge=0,
        le=300,
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=1,
        le=1440,
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=90,
    )

    login_max_failed_attempts: int = Field(
        default=5,
        ge=3,
        le=20,
    )
    login_lock_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
    )

    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    cors_allowed_origins: str = ""
    cors_allow_credentials: bool = True
    trusted_proxy_ips: str = ""

    max_request_body_bytes: int = Field(
        default=1_048_576,
        ge=1024,
        le=50_000_000,
    )
    security_headers_enabled: bool = True
    hsts_enabled: bool = False
    hsts_max_age_seconds: int = Field(
        default=31_536_000,
        ge=0,
        le=63_072_000,
    )

    auth_rate_limit_enabled: bool = False
    auth_rate_limit_requests: int = Field(
        default=120,
        ge=1,
        le=10_000,
    )
    auth_rate_limit_window_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _csv_values(value: str) -> tuple[str, ...]:
        return tuple(item.strip() for item in value.split(",") if item.strip())

    @property
    def is_production(self) -> bool:
        return self.app_environment.strip().lower() in PRODUCTION_ENVIRONMENTS

    @property
    def allowed_host_list(self) -> list[str]:
        return list(self._csv_values(self.allowed_hosts))

    @property
    def cors_origin_list(self) -> list[str]:
        return list(self._csv_values(self.cors_allowed_origins))

    @property
    def trusted_proxy_list(self) -> tuple[str, ...]:
        return self._csv_values(self.trusted_proxy_ips)

    @model_validator(mode="after")
    def validate_security_configuration(
        self,
    ) -> "Settings":
        self.app_environment = self.app_environment.strip().lower()
        self.api_v1_prefix = "/" + self.api_v1_prefix.strip("/")

        if self.jwt_algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise ValueError("JWT_ALGORITHM must be HS256, HS384 or HS512.")

        if not self.jwt_issuer.strip():
            raise ValueError("JWT_ISSUER cannot be empty.")

        if not self.jwt_audience.strip():
            raise ValueError("JWT_AUDIENCE cannot be empty.")

        allowed_hosts = self.allowed_host_list
        cors_origins = self.cors_origin_list

        if "*" in cors_origins and self.cors_allow_credentials:
            raise ValueError(
                "CORS credentials cannot be enabled "
                "when CORS_ALLOWED_ORIGINS contains '*'."
            )

        if self.is_production:
            if self.app_debug:
                raise ValueError("APP_DEBUG must be false in production.")

            normalized_secret = self.jwt_secret_key.strip().lower()
            if (
                len(self.jwt_secret_key) < 32
                or normalized_secret in INSECURE_SECRET_VALUES
            ):
                raise ValueError(
                    "JWT_SECRET_KEY must be a strong "
                    "value of at least 32 characters "
                    "in production."
                )

            if (
                not allowed_hosts
                or "*" in allowed_hosts
                or allowed_hosts
                == [
                    "localhost",
                    "127.0.0.1",
                    "testserver",
                ]
            ):
                raise ValueError(
                    "ALLOWED_HOSTS must contain the "
                    "real production hosts and cannot "
                    "contain '*'."
                )

            if not self.jwt_validate_issuer_audience:
                raise ValueError(
                    "JWT_VALIDATE_ISSUER_AUDIENCE must be true in production."
                )

            if not self.auth_rate_limit_enabled:
                raise ValueError("AUTH_RATE_LIMIT_ENABLED must be true in production.")

        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached application settings object."""

    return Settings()
