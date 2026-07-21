from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.audit.constants import (
    AuditAction,
    AuditOutcome,
    AuditSeverity,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index(
            "ix_audit_logs_farm_occurred",
            "farm_id",
            "occurred_at",
        ),
        Index(
            "ix_audit_logs_farm_module_action",
            "farm_id",
            "module",
            "action",
        ),
        Index(
            "ix_audit_logs_actor_occurred",
            "actor_user_id",
            "occurred_at",
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
        index=True,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_username: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=AuditAction.SYSTEM.value,
        index=True,
    )
    outcome: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditOutcome.SUCCESS.value,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AuditSeverity.INFO.value,
        index=True,
    )
    module: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )
    resource_type: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    resource_id: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    request_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
    )
    request_method: Mapped[str | None] = mapped_column(
        String(12),
        nullable=True,
    )
    request_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    before_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    after_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    changes: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    @property
    def is_successful(self) -> bool:
        return self.outcome == AuditOutcome.SUCCESS.value

    @property
    def is_failure(self) -> bool:
        return self.outcome in {
            AuditOutcome.FAILURE.value,
            AuditOutcome.DENIED.value,
        }
