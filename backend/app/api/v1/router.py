from datetime import UTC, datetime

from fastapi import APIRouter

from app.core.config import get_settings


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
