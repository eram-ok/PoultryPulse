from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.core.config import Settings
from app.core.network import (
    resolve_client_ip_from_scope,
)
from app.core.security import (
    create_access_token,
    decode_token,
)
from app.core.security_middleware import (
    SecurityHardeningMiddleware,
)
from app.main import app


def test_application_returns_security_headers() -> None:
    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == ("no-referrer")
    assert response.headers["x-request-id"]


def test_authentication_responses_disable_caching() -> None:
    response = TestClient(app).post(
        "/api/v1/auth/login",
        data={
            "username": "missing",
            "password": "missing",
        },
    )

    assert response.status_code == 401
    assert "no-store" in response.headers["cache-control"]
    assert response.headers["pragma"] == "no-cache"


def test_request_size_limit_rejects_large_body() -> None:
    test_app = FastAPI()
    test_app.add_middleware(
        SecurityHardeningMiddleware,
        max_request_body_bytes=16,
        security_headers_enabled=True,
        hsts_enabled=False,
        hsts_max_age_seconds=0,
        auth_rate_limit_enabled=False,
        auth_rate_limit_requests=10,
        auth_rate_limit_window_seconds=60,
    )

    @test_app.post("/echo")
    async def echo() -> dict[str, bool]:
        return {"ok": True}

    response = TestClient(test_app).post(
        "/echo",
        content=b"x" * 17,
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == ("request_body_too_large")


def test_authentication_rate_limit() -> None:
    test_app = FastAPI()
    test_app.add_middleware(
        SecurityHardeningMiddleware,
        max_request_body_bytes=1024,
        security_headers_enabled=True,
        hsts_enabled=False,
        hsts_max_age_seconds=0,
        auth_rate_limit_enabled=True,
        auth_rate_limit_requests=2,
        auth_rate_limit_window_seconds=60,
        api_v1_prefix="/api/v1",
    )

    @test_app.post("/api/v1/auth/login")
    async def login() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(test_app)

    assert client.post("/api/v1/auth/login").status_code == 200
    assert client.post("/api/v1/auth/login").status_code == 200

    limited = client.post("/api/v1/auth/login")
    assert limited.status_code == 429
    assert limited.headers["retry-after"]
    assert limited.json()["error"]["code"] == ("authentication_rate_limited")


def test_untrusted_peer_cannot_spoof_forwarded_ip() -> None:
    resolved = resolve_client_ip_from_scope(
        headers=[
            (
                b"x-forwarded-for",
                b"203.0.113.10",
            )
        ],
        client=("198.51.100.20", 12345),
        trusted_proxy_entries=(),
    )

    assert resolved == "198.51.100.20"


def test_trusted_proxy_can_supply_forwarded_ip() -> None:
    resolved = resolve_client_ip_from_scope(
        headers=[
            (
                b"x-forwarded-for",
                b"203.0.113.10, 198.51.100.20",
            )
        ],
        client=("127.0.0.1", 12345),
        trusted_proxy_entries=("127.0.0.1",),
    )

    assert resolved == "203.0.113.10"


def test_new_tokens_include_issuer_and_audience() -> None:
    token = create_access_token("security-test")
    payload = decode_token(token)

    assert payload["iss"]
    assert payload["aud"]
    assert payload["type"] == "access"


def test_production_rejects_insecure_defaults() -> None:
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            app_environment="production",
            app_debug=True,
            database_user="user",
            database_password="password",
            database_url=("postgresql://user:password@localhost/db"),
            jwt_secret_key="short",
        )


def test_development_settings_remain_compatible() -> None:
    settings = Settings(
        _env_file=None,
        database_user="user",
        database_password="password",
        database_url=("postgresql://user:password@localhost/db"),
        jwt_secret_key=("development-secret-not-for-production"),
    )

    assert settings.is_production is False
    assert "testserver" in settings.allowed_host_list
    assert settings.auth_rate_limit_enabled is False
