from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.modules.jobs.constants import BackgroundJobName


@dataclass(frozen=True, slots=True)
class BackgroundJobDefinition:
    name: str
    enabled: bool
    per_farm: bool
    interval_seconds: int


def background_job_definitions(
    settings: Settings,
) -> tuple[BackgroundJobDefinition, ...]:
    return (
        BackgroundJobDefinition(
            name=BackgroundJobName.ALERT_REFRESH.value,
            enabled=(
                settings.background_jobs_enabled and settings.alert_refresh_job_enabled
            ),
            per_farm=True,
            interval_seconds=(settings.alert_refresh_interval_minutes * 60),
        ),
        BackgroundJobDefinition(
            name=(BackgroundJobName.NOTIFICATION_DELIVERY.value),
            enabled=(
                settings.background_jobs_enabled
                and settings.notification_delivery_job_enabled
            ),
            per_farm=True,
            interval_seconds=(settings.notification_delivery_interval_seconds),
        ),
        BackgroundJobDefinition(
            name=(BackgroundJobName.JOB_HISTORY_CLEANUP.value),
            enabled=(
                settings.background_jobs_enabled
                and settings.job_history_cleanup_enabled
            ),
            per_farm=False,
            interval_seconds=(settings.job_history_cleanup_interval_hours * 3600),
        ),
    )
