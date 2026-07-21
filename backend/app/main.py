from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import (
    TrustedHostMiddleware,
)

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.database import dispose_database_engine
from app.core.exception_handlers import (
    application_error_handler,
)
from app.core.exceptions import ApplicationError
from app.core.health import check_database_readiness
from app.core.logging import configure_logging
from app.core.operational_middleware import (
    OperationalRequestLoggingMiddleware,
)
from app.core.security_middleware import (
    SecurityHardeningMiddleware,
)
from app.core.unexpected_errors import (
    unexpected_exception_handler,
)
from app.modules.audit.commercial_registry import (
    install_commercial_auditing,
)
from app.modules.audit.middleware import (
    AuditRequestContextMiddleware,
)
from app.modules.audit.operational_registry import (
    install_operational_auditing,
)


settings = get_settings()
configure_logging(
    level=settings.log_level,
    log_format=settings.log_format,
    include_uvicorn_access_logs=(settings.uvicorn_access_log_enabled),
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    _app: FastAPI,
) -> AsyncIterator[None]:
    """Log lifecycle events and release pooled resources."""

    logger.info(
        "PoultryPulse application starting.",
        extra={
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_environment,
            "event": "application_starting",
        },
    )

    try:
        if settings.startup_database_check_enabled:
            database = await check_database_readiness(
                timeout_seconds=(settings.readiness_database_timeout_seconds),
            )
            database_up = database["status"] == "up"
            logger.log(
                (logging.INFO if database_up else logging.ERROR),
                "Startup database check completed.",
                extra={
                    "database_status": database["status"],
                    "duration_ms": database.get(
                        "latency_ms",
                    ),
                    "event": ("startup_database_check_completed"),
                },
            )

            if not database_up and settings.startup_database_check_required:
                raise RuntimeError("The required startup database check did not pass.")

        logger.info(
            "PoultryPulse application started.",
            extra={
                "application": settings.app_name,
                "version": settings.app_version,
                "environment": settings.app_environment,
                "event": "application_started",
            },
        )
        yield
    finally:
        logger.info(
            "PoultryPulse application stopping.",
            extra={
                "application": settings.app_name,
                "version": settings.app_version,
                "environment": settings.app_environment,
                "event": "application_stopping",
            },
        )
        dispose_database_engine()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "PoultryPulse is a poultry management system "
        "designed primarily for layer poultry farms."
    ),
    debug=settings.app_debug,
    docs_url=("/docs" if settings.docs_enabled else None),
    redoc_url=("/redoc" if settings.docs_enabled else None),
    openapi_url=("/openapi.json" if settings.docs_enabled else None),
    lifespan=lifespan,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_host_list,
)

if settings.cors_origin_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=(settings.cors_allow_credentials),
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID"],
    )

app.add_middleware(
    SecurityHardeningMiddleware,
    max_request_body_bytes=(settings.max_request_body_bytes),
    security_headers_enabled=(settings.security_headers_enabled),
    hsts_enabled=settings.hsts_enabled,
    hsts_max_age_seconds=(settings.hsts_max_age_seconds),
    auth_rate_limit_enabled=(settings.auth_rate_limit_enabled),
    auth_rate_limit_requests=(settings.auth_rate_limit_requests),
    auth_rate_limit_window_seconds=(settings.auth_rate_limit_window_seconds),
    trusted_proxy_entries=(settings.trusted_proxy_list),
    api_v1_prefix=settings.api_v1_prefix,
)

health_paths = (
    f"{settings.api_v1_prefix}/health",
    f"{settings.api_v1_prefix}/health/live",
    f"{settings.api_v1_prefix}/health/ready",
)
app.add_middleware(
    OperationalRequestLoggingMiddleware,
    enabled=settings.request_logging_enabled,
    trusted_proxy_entries=(settings.trusted_proxy_list),
    excluded_paths=(settings.request_logging_excluded_path_list),
    health_paths=health_paths,
)

app.add_middleware(AuditRequestContextMiddleware)

app.add_exception_handler(
    ApplicationError,
    application_error_handler,
)
app.add_exception_handler(
    Exception,
    unexpected_exception_handler,
)


@app.get(
    "/",
    tags=["System"],
    summary="PoultryPulse API welcome endpoint",
)
def root() -> dict[str, str | None]:
    """Return basic information about the API."""

    return {
        "message": ("Welcome to the PoultryPulse API"),
        "tagline": ("Know Your Flock. Grow Your Farm."),
        "documentation": ("/docs" if settings.docs_enabled else None),
    }


app.include_router(
    api_v1_router,
    prefix=settings.api_v1_prefix,
)

# Stage 17C1: install farm-operation audit wrappers after
# all API routers and service modules have been imported.
install_operational_auditing()

# Stage 17C2: install sales, finance, alert and
# notification audit wrappers.
install_commercial_auditing()
