from __future__ import annotations

import logging
import os
import socket
import time
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import SessionLocal
from app.core.exceptions import (
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.modules.alerts.service import AlertsService
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)
from app.modules.audit.service import AuditService
from app.modules.jobs.constants import (
    BackgroundJobName,
    BackgroundJobStatus,
    BackgroundJobTrigger,
)
from app.modules.jobs.definitions import (
    BackgroundJobDefinition,
    background_job_definitions,
)
from app.modules.jobs.locking import background_job_lock
from app.modules.jobs.models import BackgroundJobRun
from app.modules.jobs.repository import (
    BackgroundJobsRepository,
)


logger = logging.getLogger(__name__)


def worker_identity() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _json_result(value: Any) -> dict[str, Any]:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    if value is None:
        return {}
    return {"result": value}


class BackgroundJobsService:
    def __init__(
        self,
        database_session: Session,
        *,
        settings: Settings | None = None,
    ) -> None:
        self.database_session = database_session
        self.settings = settings or get_settings()
        self.repository = BackgroundJobsRepository(
            database_session,
        )

    @property
    def definitions(
        self,
    ) -> tuple[BackgroundJobDefinition, ...]:
        return background_job_definitions(
            self.settings,
        )

    def definition(
        self,
        job_name: str,
    ) -> BackgroundJobDefinition:
        for item in self.definitions:
            if item.name == job_name:
                return item
        raise ResourceNotFoundError(
            "The selected background job does not exist.",
            error_code="background_job_not_found",
        )

    def _execute_handler(
        self,
        *,
        job_name: str,
        farm_id: UUID | None,
    ) -> dict[str, Any]:
        if job_name == (BackgroundJobName.ALERT_REFRESH.value):
            if farm_id is None:
                raise ValueError("The alert refresh job requires a farm.")
            result = AlertsService(
                self.database_session,
            ).refresh(
                farm_id,
                None,
                as_of_date=None,
                send_now=False,
            )
            return _json_result(result)

        if job_name == (BackgroundJobName.NOTIFICATION_DELIVERY.value):
            if farm_id is None:
                raise ValueError("The delivery job requires a farm.")
            result = AlertsService(
                self.database_session,
            ).process_deliveries(
                farm_id,
                actor_user_id=None,
                limit=(self.settings.notification_delivery_batch_size),
            )
            return _json_result(result)

        if job_name == (BackgroundJobName.JOB_HISTORY_CLEANUP.value):
            deleted = self.repository.delete_old_runs(
                retention_days=(self.settings.job_history_retention_days),
            )
            self.database_session.commit()
            return {"deleted_runs": deleted}

        raise ResourceNotFoundError(
            "The selected background job does not exist.",
            error_code="background_job_not_found",
        )

    def _record_audit(
        self,
        *,
        run: BackgroundJobRun,
    ) -> None:
        AuditService(self.database_session).record(
            module="background_jobs",
            action=AuditAction.SYSTEM,
            description=(
                f"Background job {run.job_name} finished with status {run.status}."
            ),
            outcome=(
                AuditOutcome.SUCCESS if run.is_successful else AuditOutcome.FAILURE
            ),
            severity=(
                AuditSeverity.INFO if run.is_successful else AuditSeverity.WARNING
            ),
            farm_id=run.farm_id,
            resource_type="BackgroundJobRun",
            resource_id=run.id,
            metadata={
                "job_name": run.job_name,
                "trigger": run.trigger,
                "duration_ms": run.duration_ms,
                "worker_id": run.worker_id,
            },
            error_code=("background_job_failed" if run.is_failed else None),
            error_message=run.error_message,
            commit=False,
        )

    def run(
        self,
        *,
        job_name: str,
        farm_id: UUID | None,
        trigger: str,
        force: bool,
        scheduled_for: datetime | None = None,
    ) -> BackgroundJobRun | None:
        definition = self.definition(job_name)

        if definition.per_farm and farm_id is None:
            raise ValueError(f"The {job_name} job requires a farm_id.")
        if not definition.per_farm:
            farm_id = None

        now = datetime.now(UTC)

        with background_job_lock(
            self.database_session,
            job_name=job_name,
            farm_id=farm_id,
        ) as acquired:
            if not acquired:
                if force:
                    raise ResourceConflictError(
                        "The background job is already running.",
                        error_code=("background_job_already_running"),
                    )
                return None

            if not force and not self.repository.is_due(
                job_name=job_name,
                farm_id=farm_id,
                interval_seconds=(definition.interval_seconds),
                now=now,
            ):
                return None

            run = BackgroundJobRun(
                farm_id=farm_id,
                job_name=job_name,
                status=(BackgroundJobStatus.RUNNING.value),
                trigger=trigger,
                scheduled_for=scheduled_for,
                started_at=now,
                worker_id=worker_identity(),
            )
            self.repository.add_run(run)
            self.database_session.commit()

            started = time.perf_counter()
            try:
                result = self._execute_handler(
                    job_name=job_name,
                    farm_id=farm_id,
                )
                run.status = BackgroundJobStatus.SUCCESS.value
                run.result_json = result
                run.error_type = None
                run.error_message = None
            except Exception as error:
                self.database_session.rollback()
                run = self.repository.get_run(run.id)
                if run is None:
                    raise
                run.status = BackgroundJobStatus.FAILURE.value
                run.error_type = type(error).__name__
                run.error_message = str(error)[:4000]
                logger.exception(
                    "Background job failed.",
                    extra={
                        "job_name": job_name,
                        "job_run_id": str(run.id),
                        "job_status": run.status,
                        "worker_id": run.worker_id,
                        "event": "background_job_failed",
                    },
                )
            finally:
                completed = datetime.now(UTC)
                run.completed_at = completed
                run.duration_ms = max(
                    0,
                    round((time.perf_counter() - started) * 1000),
                )
                self.database_session.commit()

                try:
                    self._record_audit(run=run)
                    self.database_session.commit()
                except Exception:
                    self.database_session.rollback()
                    logger.exception(
                        "Background job audit recording failed.",
                        extra={
                            "job_name": job_name,
                            "job_run_id": str(run.id),
                            "job_status": run.status,
                            "worker_id": run.worker_id,
                            "event": ("background_job_audit_failed"),
                        },
                    )

            logger.info(
                "Background job completed.",
                extra={
                    "job_name": job_name,
                    "job_run_id": str(run.id),
                    "job_status": run.status,
                    "worker_id": run.worker_id,
                    "duration_ms": run.duration_ms,
                    "event": "background_job_completed",
                },
            )
            return run

    def run_scheduled_definition(
        self,
        definition: BackgroundJobDefinition,
    ) -> list[BackgroundJobRun]:
        if not definition.enabled:
            return []

        targets: list[UUID | None]
        if definition.per_farm:
            targets = list(self.repository.farm_ids())
        else:
            targets = [None]

        completed: list[BackgroundJobRun] = []
        for farm_id in targets:
            run = self.run(
                job_name=definition.name,
                farm_id=farm_id,
                trigger=(BackgroundJobTrigger.SCHEDULED.value),
                force=False,
                scheduled_for=datetime.now(UTC),
            )
            if run is not None:
                completed.append(run)
        return completed


def execute_scheduled_definition(
    definition: BackgroundJobDefinition,
) -> list[BackgroundJobRun]:
    with SessionLocal() as database_session:
        return BackgroundJobsService(
            database_session,
        ).run_scheduled_definition(definition)
