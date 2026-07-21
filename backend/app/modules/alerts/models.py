from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.alerts.constants import (
    AlertDeliveryChannel,
    AlertRefreshStatus,
    AlertStatus,
)
from app.modules.reports.constants import (
    AlertSeverity,
    AlertType,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class OperationalAlert(Base):
    __tablename__ = "operational_alerts"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "fingerprint",
            name="uq_operational_alerts_farm_fingerprint",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fingerprint: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AlertType.LOW_FEED_STOCK.value,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertSeverity.INFO.value,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertStatus.OPEN.value,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_module: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    action_path: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    assigned_to: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    last_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    occurrence_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    acknowledged_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    @property
    def is_open(self) -> bool:
        return self.status == AlertStatus.OPEN.value

    @property
    def is_acknowledged(self) -> bool:
        return self.status == AlertStatus.ACKNOWLEDGED.value

    @property
    def is_resolved(self) -> bool:
        return self.status == AlertStatus.RESOLVED.value

    @property
    def is_critical(self) -> bool:
        return self.severity == AlertSeverity.CRITICAL.value


class AlertUserState(Base):
    __tablename__ = "alert_user_states"
    __table_args__ = (
        UniqueConstraint(
            "alert_id",
            "user_id",
            name="uq_alert_user_states_alert_user",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "operational_alerts.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_dismissed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "user_id",
            "alert_type",
            "channel",
            name=("uq_notification_preferences_user_type_channel"),
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=AlertType.LOW_FEED_STOCK.value,
    )
    channel: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertDeliveryChannel.IN_APP.value,
    )
    minimum_severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertSeverity.INFO.value,
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )


class AlertRefreshRun(Base):
    __tablename__ = "alert_refresh_runs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    farm_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=AlertRefreshStatus.RUNNING.value,
        index=True,
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
    detected_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    updated_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    resolved_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    @property
    def is_completed(self) -> bool:
        return self.status == AlertRefreshStatus.COMPLETED.value

    @property
    def is_failed(self) -> bool:
        return self.status == AlertRefreshStatus.FAILED.value
