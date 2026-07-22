from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.health import check_database_readiness
from app.modules.alerts.router import (
    router as alerts_router,
)
from app.modules.audit.router import (
    router as audit_router,
)
from app.modules.auth.router import router as auth_router
from app.modules.bird_losses.router import (
    router as bird_losses_router,
)
from app.modules.eggs.router import router as eggs_router
from app.modules.farms.router import router as farms_router
from app.modules.feed.router import router as feed_router
from app.modules.finance.router import (
    router as finance_router,
)
from app.modules.flocks.router import (
    router as flocks_router,
)
from app.modules.health.router import (
    router as health_router,
)
from app.modules.jobs.router import router as jobs_router
from app.modules.houses.router import (
    router as houses_router,
)
from app.modules.platform.router import (
    router as platform_router,
)
from app.modules.production.router import (
    router as production_router,
)
from app.modules.reports.advanced_router import (
    router as advanced_reports_router,
)
from app.modules.reports.router import (
    router as reports_router,
)
from app.modules.sales.router import (
    router as sales_router,
)
from app.modules.suppliers.router import (
    router as suppliers_router,
)
from app.modules.users.router import (
    roles_router,
    router as users_router,
)


settings = get_settings()

router = APIRouter()


def _base_health_payload() -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get(
    "/health",
    tags=["System"],
    summary="Check the API status",
)
def health_check() -> dict[str, str]:
    """Keep the original lightweight health response."""

    return {
        "status": "healthy",
        **_base_health_payload(),
    }


@router.get(
    "/health/live",
    tags=["System"],
    summary="Check whether the API process is alive",
)
def liveness_check() -> dict[str, str]:
    """Return success without calling external dependencies."""

    return {
        "status": "alive",
        **_base_health_payload(),
    }


@router.get(
    "/health/ready",
    tags=["System"],
    summary="Check whether the API is ready for traffic",
)
async def readiness_check(
    response: Response,
) -> dict[str, Any]:
    """Check database availability before accepting traffic."""

    database = await check_database_readiness(
        timeout_seconds=(settings.readiness_database_timeout_seconds),
    )
    ready = database["status"] == "up"

    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": ("ready" if ready else "not_ready"),
        **_base_health_payload(),
        "checks": {
            "database": database,
        },
    }


router.include_router(auth_router)
router.include_router(platform_router)
router.include_router(users_router)
router.include_router(roles_router)
router.include_router(farms_router)
router.include_router(houses_router)
router.include_router(suppliers_router)
router.include_router(flocks_router)
router.include_router(production_router)
router.include_router(eggs_router)
router.include_router(feed_router)
router.include_router(bird_losses_router)
router.include_router(health_router)
router.include_router(sales_router)
router.include_router(finance_router)
router.include_router(reports_router)
router.include_router(advanced_reports_router)
router.include_router(alerts_router)
router.include_router(jobs_router)
router.include_router(audit_router)
