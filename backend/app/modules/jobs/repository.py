from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session

from app.modules.jobs.models import BackgroundJobRun


class BackgroundJobsRepository:
    def __init__(self, database_session: Session) -> None:
        self.database_session = database_session

    def farm_ids(self) -> list[UUID]:
        return list(
            self.database_session.execute(
                text("SELECT id FROM farms ORDER BY id")
            ).scalars()
        )

    def latest_run(
        self,
        *,
        job_name: str,
        farm_id: UUID | None,
    ) -> BackgroundJobRun | None:
        conditions = [
            BackgroundJobRun.job_name == job_name,
        ]
        if farm_id is None:
            conditions.append(BackgroundJobRun.farm_id.is_(None))
        else:
            conditions.append(BackgroundJobRun.farm_id == farm_id)

        return self.database_session.scalar(
            select(BackgroundJobRun)
            .where(*conditions)
            .order_by(BackgroundJobRun.started_at.desc())
            .limit(1)
        )

    def is_due(
        self,
        *,
        job_name: str,
        farm_id: UUID | None,
        interval_seconds: int,
        now: datetime,
    ) -> bool:
        latest = self.latest_run(
            job_name=job_name,
            farm_id=farm_id,
        )
        if latest is None:
            return True
        return latest.started_at <= now - timedelta(
            seconds=interval_seconds,
        )

    def add_run(
        self,
        run: BackgroundJobRun,
    ) -> BackgroundJobRun:
        self.database_session.add(run)
        self.database_session.flush()
        return run

    def get_run(
        self,
        run_id: UUID,
    ) -> BackgroundJobRun | None:
        return self.database_session.get(
            BackgroundJobRun,
            run_id,
        )

    def list_runs(
        self,
        *,
        offset: int,
        limit: int,
        job_name: str | None,
        status: str | None,
        farm_id: UUID | None,
    ) -> tuple[list[BackgroundJobRun], int]:
        conditions = []
        if job_name is not None:
            conditions.append(
                BackgroundJobRun.job_name == job_name,
            )
        if status is not None:
            conditions.append(
                BackgroundJobRun.status == status,
            )
        if farm_id is not None:
            conditions.append(
                BackgroundJobRun.farm_id == farm_id,
            )

        rows = (
            select(BackgroundJobRun)
            .where(*conditions)
            .order_by(BackgroundJobRun.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        total = select(func.count(BackgroundJobRun.id)).where(*conditions)

        return (
            list(self.database_session.scalars(rows).all()),
            int(self.database_session.scalar(total) or 0),
        )

    def delete_old_runs(
        self,
        *,
        retention_days: int,
    ) -> int:
        cutoff = datetime.now(UTC) - timedelta(
            days=retention_days,
        )
        result = self.database_session.execute(
            delete(BackgroundJobRun).where(
                BackgroundJobRun.started_at < cutoff,
            )
        )
        return int(result.rowcount or 0)
