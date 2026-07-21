from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.jobs.constants import (
    BackgroundJobStatus,
    BackgroundJobTrigger,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class BackgroundJobRun(Base):
    __tablename__ = "background_job_runs"
    __table_args__ = (
        Index(
            "ix_background_job_runs_job_started",
            "job_name",
            "started_at",
        ),
        Index(
            "ix_background_job_runs_farm_started",
            "farm_id",
            "started_at",
        ),
        Index(
            "ix_background_job_runs_status_started",
            "status",
            "started_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="SET NULL"),
        nullable=True,
    )
    job_name: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BackgroundJobStatus.RUNNING.value,
    )
    trigger: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=BackgroundJobTrigger.SCHEDULED.value,
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    result_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error_type: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    worker_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    @property
    def is_running(self) -> bool:
        return self.status == BackgroundJobStatus.RUNNING.value

    @property
    def is_successful(self) -> bool:
        return self.status == BackgroundJobStatus.SUCCESS.value

    @property
    def is_failed(self) -> bool:
        return self.status == BackgroundJobStatus.FAILURE.value
