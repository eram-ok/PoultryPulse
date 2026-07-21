from app.modules.audit.middleware import AuditRequestContextMiddleware
from app.modules.audit.operational_registry import (
    install_operational_auditing,
)
from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exception_handlers import application_error_handler
from app.core.exceptions import ApplicationError

from app.modules.audit.commercial_registry import (
    install_commercial_auditing,
)


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "PoultryPulse is a poultry management system designed primarily "
        "for layer poultry farms."
    ),
    debug=settings.app_debug,
)

app.add_middleware(AuditRequestContextMiddleware)

app.add_exception_handler(
    ApplicationError,
    application_error_handler,
)


@app.get(
    "/",
    tags=["System"],
    summary="PoultryPulse API welcome endpoint",
)
def root() -> dict[str, str]:
    """Return basic information about the API."""

    return {
        "message": "Welcome to the PoultryPulse API",
        "tagline": "Know Your Flock. Grow Your Farm.",
        "documentation": "/docs",
    }


app.include_router(
    api_v1_router,
    prefix=settings.api_v1_prefix,
)

# Stage 17C1: install farm-operation audit wrappers after
# all API routers and service modules have been imported.
install_operational_auditing()

# Stage 17C2: install sales, finance, alert and notification audit wrappers.
install_commercial_auditing()
