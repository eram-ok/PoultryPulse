from __future__ import annotations

import asyncio
import logging

from app.core.config import Settings, get_settings
from app.modules.jobs.definitions import (
    background_job_definitions,
)
from app.modules.jobs.service import (
    execute_scheduled_definition,
)


logger = logging.getLogger(__name__)


class BackgroundJobScheduler:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def run_iteration(self) -> int:
        executed = 0
        for definition in background_job_definitions(
            self.settings,
        ):
            if not definition.enabled:
                continue
            runs = await asyncio.to_thread(
                execute_scheduled_definition,
                definition,
            )
            executed += len(runs)
        return executed

    async def run_forever(self) -> None:
        logger.info(
            "Background job scheduler started.",
            extra={
                "event": "background_job_scheduler_started",
            },
        )
        try:
            while not self._stop_event.is_set():
                try:
                    await self.run_iteration()
                except Exception:
                    logger.exception(
                        "Background scheduler iteration failed.",
                        extra={
                            "event": ("background_job_scheduler_iteration_failed"),
                        },
                    )

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=(self.settings.background_job_poll_seconds),
                    )
                except TimeoutError:
                    continue
        finally:
            logger.info(
                "Background job scheduler stopped.",
                extra={
                    "event": ("background_job_scheduler_stopped"),
                },
            )

    async def start(self) -> None:
        if self.is_running:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(
            self.run_forever(),
            name="poultrypulse-background-jobs",
        )

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task is not None:
            await self._task
            self._task = None


_embedded_scheduler: BackgroundJobScheduler | None = None


def get_embedded_scheduler() -> BackgroundJobScheduler:
    global _embedded_scheduler
    if _embedded_scheduler is None:
        _embedded_scheduler = BackgroundJobScheduler()
    return _embedded_scheduler
