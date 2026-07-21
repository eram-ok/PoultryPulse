from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.core.config import get_settings


logger = logging.getLogger(__name__)
settings = get_settings()


def _engine_options() -> dict[str, Any]:
    database_backend = make_url(
        settings.database_url,
    ).get_backend_name()
    options: dict[str, Any] = {
        "pool_pre_ping": True,
        "pool_recycle": (settings.database_pool_recycle_seconds),
        "pool_reset_on_return": "rollback",
        "echo": False,
    }

    if database_backend != "sqlite":
        options.update(
            {
                "pool_size": (settings.database_pool_size),
                "max_overflow": (settings.database_max_overflow),
                "pool_timeout": (settings.database_pool_timeout_seconds),
                "pool_use_lifo": True,
            }
        )

    if database_backend == "postgresql":
        options["connect_args"] = {
            "connect_timeout": (settings.database_connect_timeout_seconds)
        }

    return options


engine = create_engine(
    settings.database_url,
    **_engine_options(),
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class inherited by all PoultryPulse models."""

    pass


def dispose_database_engine() -> None:
    """Close pooled database connections during shutdown."""

    engine.dispose()
    logger.info(
        "Database connection pool disposed.",
        extra={
            "event": "database_engine_disposed",
        },
    )


def database_pool_status() -> dict[str, int | None]:
    """Return non-secret connection-pool diagnostics."""

    pool = engine.pool

    def safe_value(
        method_name: str,
    ) -> int | None:
        method = getattr(
            pool,
            method_name,
            None,
        )
        if not callable(method):
            return None

        try:
            return int(method())
        except (TypeError, ValueError):
            return None

    return {
        "size": safe_value("size"),
        "checked_in": safe_value("checkedin"),
        "checked_out": safe_value("checkedout"),
        "overflow": safe_value("overflow"),
    }


def get_database_session() -> Generator[Session, None, None]:
    """Create and safely close a request database session."""

    database_session = SessionLocal()

    try:
        yield database_session
    except Exception:
        database_session.rollback()
        raise
    finally:
        database_session.close()
