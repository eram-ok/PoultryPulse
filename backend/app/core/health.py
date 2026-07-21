from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import text

from app.core.database import engine


logger = logging.getLogger(__name__)


def _database_probe() -> None:
    with engine.connect() as connection:
        value = connection.execute(
            text("SELECT 1"),
        ).scalar_one()

    if value != 1:
        raise RuntimeError(
            "The database readiness query returned an unexpected result."
        )


async def check_database_readiness(
    *,
    timeout_seconds: float,
) -> dict[str, Any]:
    """Check database availability without exposing connection details."""

    started_at = time.perf_counter()

    try:
        await asyncio.wait_for(
            asyncio.to_thread(_database_probe),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        latency_ms = round(
            (time.perf_counter() - started_at) * 1000,
            3,
        )
        logger.warning(
            "Database readiness check timed out.",
            extra={
                "database_status": "down",
                "duration_ms": latency_ms,
                "event": "database_readiness_timeout",
            },
        )
        return {
            "status": "down",
            "reason": "timeout",
            "latency_ms": latency_ms,
        }
    except Exception as error:
        latency_ms = round(
            (time.perf_counter() - started_at) * 1000,
            3,
        )
        logger.warning(
            "Database readiness check failed.",
            extra={
                "database_status": "down",
                "duration_ms": latency_ms,
                "error_type": type(error).__name__,
                "event": "database_readiness_failed",
            },
            exc_info=True,
        )
        return {
            "status": "down",
            "reason": "connection_failed",
            "latency_ms": latency_ms,
        }

    latency_ms = round(
        (time.perf_counter() - started_at) * 1000,
        3,
    )
    return {
        "status": "up",
        "latency_ms": latency_ms,
    }
