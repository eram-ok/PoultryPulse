from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.modules.jobs.constants import (
    BackgroundJobName,
    BackgroundJobStatus,
    BackgroundJobTrigger,
)
from app.modules.jobs.definitions import (
    background_job_definitions,
)
from app.modules.jobs.locking import advisory_lock_key
from app.modules.jobs.models import BackgroundJobRun
from app.modules.jobs.scheduler import (
    BackgroundJobScheduler,
)
from app.modules.jobs.service import BackgroundJobsService


def test_background_job_definitions() -> None:
    settings = Settings(
        _env_file=None,
        database_user="user",
        database_password="password",
        database_url=("sqlite+pysqlite:///:memory:"),
        jwt_secret_key=("development-secret-not-for-production"),
    )

    definitions = background_job_definitions(settings)

    assert len(definitions) == 3
    assert definitions[0].name == (BackgroundJobName.ALERT_REFRESH.value)
    assert definitions[0].per_farm is True
    assert definitions[2].per_farm is False


def test_advisory_lock_key_is_stable() -> None:
    farm_id = uuid4()

    first = advisory_lock_key(
        job_name="alert_refresh",
        farm_id=farm_id,
    )
    second = advisory_lock_key(
        job_name="alert_refresh",
        farm_id=farm_id,
    )

    assert first == second
    assert -(2**63) <= first < 2**63


def test_manual_cleanup_job_records_success(
    database_session: Session,
) -> None:
    service = BackgroundJobsService(
        database_session,
    )

    run = service.run(
        job_name=(BackgroundJobName.JOB_HISTORY_CLEANUP.value),
        farm_id=None,
        trigger=(BackgroundJobTrigger.MANUAL.value),
        force=True,
    )

    assert run is not None
    assert run.status == (BackgroundJobStatus.SUCCESS.value)
    assert run.completed_at is not None
    assert run.result_json is not None
    assert "deleted_runs" in run.result_json

    persisted = database_session.scalar(
        select(BackgroundJobRun).where(
            BackgroundJobRun.id == run.id,
        )
    )
    assert persisted is not None


def test_due_check_suppresses_duplicate_run(
    database_session: Session,
) -> None:
    run = BackgroundJobRun(
        job_name="job_history_cleanup",
        status=BackgroundJobStatus.SUCCESS.value,
        trigger=BackgroundJobTrigger.SCHEDULED.value,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
        duration_ms=1,
        worker_id="test-worker",
    )
    database_session.add(run)
    database_session.commit()

    service = BackgroundJobsService(
        database_session,
    )
    result = service.run(
        job_name="job_history_cleanup",
        farm_id=None,
        trigger=BackgroundJobTrigger.SCHEDULED.value,
        force=False,
    )

    assert result is None


def test_scheduler_iteration_uses_thread_runner(
    monkeypatch,
) -> None:
    settings = Settings(
        _env_file=None,
        database_user="user",
        database_password="password",
        database_url=("sqlite+pysqlite:///:memory:"),
        jwt_secret_key=("development-secret-not-for-production"),
        alert_refresh_job_enabled=False,
        notification_delivery_job_enabled=False,
        background_jobs_enabled=True,
        job_history_cleanup_enabled=True,
    )
    scheduler = BackgroundJobScheduler(
        settings=settings,
    )

    calls: list[str] = []

    def fake_execute(definition):
        calls.append(definition.name)
        return []

    monkeypatch.setattr(
        "app.modules.jobs.scheduler.execute_scheduled_definition",
        fake_execute,
    )

    executed = asyncio.run(
        scheduler.run_iteration(),
    )

    assert executed == 0
    assert calls == ["job_history_cleanup"]
