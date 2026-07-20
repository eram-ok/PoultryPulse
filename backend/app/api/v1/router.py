from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.farms.router import router as farms_router
from app.modules.flocks.router import router as flocks_router
from app.modules.houses.router import router as houses_router
from app.modules.suppliers.router import (
    router as suppliers_router,
)
from app.modules.users.router import (
    roles_router,
    router as users_router,
)


settings = get_settings()

router = APIRouter()


@router.get(
    "/health",
    tags=["System"],
    summary="Check the API status",
)
def health_check() -> dict[str, str]:
    """Return the current PoultryPulse API status."""

    return {
        "status": "healthy",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_environment,
        "timestamp": datetime.now(UTC).isoformat(),
    }


router.include_router(auth_router)
router.include_router(users_router)
router.include_router(roles_router)
router.include_router(farms_router)
router.include_router(houses_router)
router.include_router(suppliers_router)
router.include_router(flocks_router)
