from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.farms.models import Farm
from app.modules.flocks.models import Flock
from app.modules.production.constants import (
    ProductionRecordStatus,
)


class DailyEggProduction(Base):
    """Represents one flock's egg production for one day."""

    __tablename__ = "daily_egg_productions"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "flock_id",
            "production_date",
            name=("uq_daily_egg_productions_farm_flock_date"),
        ),
        CheckConstraint(
            "birds_present > 0",
            name=("ck_daily_egg_productions_birds_present_positive"),
        ),
        CheckConstraint(
            "morning_eggs >= 0",
            name=("ck_daily_egg_productions_morning_nonnegative"),
        ),
        CheckConstraint(
            "afternoon_eggs >= 0",
            name=("ck_daily_egg_productions_afternoon_nonnegative"),
        ),
        CheckConstraint(
            "evening_eggs >= 0",
            name=("ck_daily_egg_productions_evening_nonnegative"),
        ),
        CheckConstraint(
            "large_eggs >= 0",
            name=("ck_daily_egg_productions_large_nonnegative"),
        ),
        CheckConstraint(
            "medium_eggs >= 0",
            name=("ck_daily_egg_productions_medium_nonnegative"),
        ),
        CheckConstraint(
            "small_eggs >= 0",
            name=("ck_daily_egg_productions_small_nonnegative"),
        ),
        CheckConstraint(
            "damaged_eggs >= 0",
            name=("ck_daily_egg_productions_damaged_nonnegative"),
        ),
        CheckConstraint(
            "rejected_eggs >= 0",
            name=("ck_daily_egg_productions_rejected_nonnegative"),
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'SUBMITTED', 'CONFIRMED', 'REJECTED', 'VOIDED')",
            name=("ck_daily_egg_productions_valid_status"),
        ),
        CheckConstraint(
            "revision_number > 0",
            name=("ck_daily_egg_productions_revision_positive"),
        ),
        Index(
            "ix_daily_egg_productions_farm_date",
            "farm_id",
            "production_date",
        ),
        Index(
            "ix_daily_egg_productions_flock_date",
            "flock_id",
            "production_date",
        ),
        Index(
            "ix_daily_egg_productions_farm_status",
            "farm_id",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flocks.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    production_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    birds_present: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    morning_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    afternoon_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    evening_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    large_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    medium_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    small_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    damaged_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    rejected_eggs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=ProductionRecordStatus.DRAFT.value,
        server_default=ProductionRecordStatus.DRAFT.value,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    revision_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )

    recorded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    last_updated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    rejected_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    voided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    voided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    @property
    def total_collected(self) -> int:
        """Return the total eggs collected during the day."""

        return self.morning_eggs + self.afternoon_eggs + self.evening_eggs

    @property
    def total_graded(self) -> int:
        """Return the total eggs assigned to grade categories."""

        return (
            self.large_eggs
            + self.medium_eggs
            + self.small_eggs
            + self.damaged_eggs
            + self.rejected_eggs
        )

    @property
    def saleable_eggs(self) -> int:
        """Return eggs considered suitable for normal sale."""

        return self.large_eggs + self.medium_eggs + self.small_eggs

    @property
    def ungraded_eggs(self) -> int:
        """Return collected eggs not yet assigned a grade."""

        return self.total_collected - self.total_graded

    @property
    def laying_percentage(self) -> Decimal:
        """Calculate hen-day laying percentage."""

        if self.birds_present <= 0:
            return Decimal("0.00")

        percentage = (
            Decimal(self.total_collected) / Decimal(self.birds_present) * Decimal("100")
        )

        return percentage.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def __repr__(self) -> str:
        return (
            "DailyEggProduction("
            f"id={self.id!r}, "
            f"flock_id={self.flock_id!r}, "
            f"production_date={self.production_date!r}, "
            f"status={self.status!r}"
            ")"
        )
