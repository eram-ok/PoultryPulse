from __future__ import annotations

import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.v1 import router as api_router
from app.core.config import Settings
from app.core.logging import JsonLogFormatter
from app.core.operational_middleware import (
    OperationalRequestLoggingMiddleware,
)
from app.main import app


def test_liveness_endpoint_is_dependency_free() -> None:
    response = TestClient(app).get(
        "/api/v1/health/live",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    assert "no-store" in response.headers["cache-control"]


def test_readiness_endpoint_reports_database_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def ready_database(
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        return {
            "status": "up",
            "latency_ms": 1.25,
        }

    monkeypatch.setattr(
        api_router,
        "check_database_readiness",
        ready_database,
    )

    response = TestClient(app).get(
        "/api/v1/health/ready",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"]["status"] == "up"
    assert "no-store" in response.headers["cache-control"]


def test_readiness_endpoint_returns_503_when_database_down(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def unavailable_database(
        *,
        timeout_seconds: float,
    ) -> dict[str, object]:
        assert timeout_seconds > 0
        return {
            "status": "down",
            "reason": "connection_failed",
            "latency_ms": 2.5,
        }

    monkeypatch.setattr(
        api_router,
        "check_database_readiness",
        unavailable_database,
    )

    response = TestClient(app).get(
        "/api/v1/health/ready",
    )

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_json_log_formatter_includes_request_context() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="poultrypulse.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Completed test request.",
        args=(),
        exc_info=None,
    )
    record.request_id = "test-request-id"
    record.status_code = 200
    record.duration_ms = 3.5

    payload = json.loads(
        formatter.format(record),
    )

    assert payload["message"] == ("Completed test request.")
    assert payload["request_id"] == "test-request-id"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 3.5


def test_request_middleware_logs_completion(
    caplog: pytest.LogCaptureFixture,
) -> None:
    test_app = FastAPI()
    test_app.add_middleware(
        OperationalRequestLoggingMiddleware,
        enabled=True,
        excluded_paths=(),
        health_paths=(),
    )

    @test_app.get("/example")
    async def example() -> dict[str, bool]:
        return {"ok": True}

    with caplog.at_level(
        logging.INFO,
        logger="poultrypulse.requests",
    ):
        response = TestClient(test_app).get(
            "/example",
            headers={
                "X-Request-ID": "middleware-test",
            },
        )

    assert response.status_code == 200

    matching_records = [
        record
        for record in caplog.records
        if record.name == "poultrypulse.requests"
        and getattr(
            record,
            "request_id",
            None,
        )
        == "middleware-test"
    ]
    assert matching_records
    assert matching_records[-1].status_code == 200
    assert matching_records[-1].request_path == "/example"


def test_operational_settings_validate_dependencies() -> None:
    with pytest.raises(
        ValueError,
        match="STARTUP_DATABASE_CHECK_ENABLED",
    ):
        Settings(
            _env_file=None,
            database_user="user",
            database_password="password",
            database_url=("postgresql://user:password@localhost/db"),
            jwt_secret_key=("development-secret-not-for-production"),
            startup_database_check_required=True,
            startup_database_check_enabled=False,
        )


def test_operational_defaults_remain_development_safe() -> None:
    settings = Settings(
        _env_file=None,
        database_user="user",
        database_password="password",
        database_url=("postgresql://user:password@localhost/db"),
        jwt_secret_key=("development-secret-not-for-production"),
    )

    assert settings.log_level == "INFO"
    assert settings.log_format == "text"
    assert settings.database_pool_size == 5
    assert settings.startup_database_check_enabled is False
