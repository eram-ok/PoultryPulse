from __future__ import annotations

import asyncio
import logging

from app.core.config import get_settings
from app.core.database import dispose_database_engine
from app.core.logging import configure_logging
from app.modules.audit.commercial_registry import (
    install_commercial_auditing,
)
from app.modules.jobs.scheduler import (
    BackgroundJobScheduler,
)


async def main() -> int:
    settings = get_settings()
    configure_logging(
        level=settings.log_level,
        log_format=settings.log_format,
        include_uvicorn_access_logs=False,
    )
    logger = logging.getLogger(__name__)
    install_commercial_auditing()

    if not settings.background_jobs_enabled:
        logger.warning(
            "Background jobs are disabled.",
            extra={
                "event": "background_jobs_disabled",
            },
        )
        return 0

    scheduler = BackgroundJobScheduler(
        settings=settings,
    )
    try:
        await scheduler.run_forever()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info(
            "Background worker shutdown requested.",
            extra={
                "event": ("background_job_worker_shutdown_requested"),
            },
        )
    finally:
        dispose_database_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
