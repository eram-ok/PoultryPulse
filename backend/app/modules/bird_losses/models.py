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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.bird_losses.constants import (
    BirdDisposalMethod,
    BirdLossReason,
    BirdLossRecordStatus,
    BirdLossType,
)
from app.modules.farms.models import Farm
from app.modules.flocks.models import (
    Flock,
    FlockPopulationTransaction,
)


class BirdLossRecord(Base):
    """Represents a mortality or culling incident."""

    __tablename__ = "bird_loss_records"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_bird_loss_quantity_positive",
        ),
        CheckConstraint(
            "population_before > 0",
            name=("ck_bird_loss_population_before_positive"),
        ),
        CheckConstraint(
            "population_after >= 0",
            name=("ck_bird_loss_population_after_nonnegative"),
        ),
        CheckConstraint(
            "population_after = population_before - quantity",
            name=("ck_bird_loss_population_reconciliation"),
        ),
        CheckConstraint(
            "loss_percentage >= 0 AND loss_percentage <= 100",
            name="ck_bird_loss_percentage_range",
        ),
        CheckConstraint(
            "loss_type IN ('MORTALITY', 'CULLING')",
            name="ck_bird_loss_valid_type",
        ),
        CheckConstraint(
            "reason_category IN ("
            "'DISEASE', "
            "'INJURY', "
            "'PREDATION', "
            "'HEAT_STRESS', "
            "'COLD_STRESS', "
            "'SUFFOCATION', "
            "'STARVATION', "
            "'DEHYDRATION', "
            "'POISONING', "
            "'LOW_PRODUCTION', "
            "'DEFORMITY', "
            "'OLD_AGE', "
            "'AGGRESSION', "
            "'VETERINARY_RECOMMENDATION', "
            "'UNKNOWN', "
            "'OTHER'"
            ")",
            name="ck_bird_loss_valid_reason",
        ),
        CheckConstraint(
            "disposal_method IN ("
            "'BURIAL', "
            "'INCINERATION', "
            "'COMPOSTING', "
            "'RENDERING', "
            "'VETERINARY_DISPOSAL', "
            "'SOLD_FOR_SLAUGHTER', "
            "'HOME_CONSUMPTION', "
            "'OTHER', "
            "'NOT_RECORDED'"
            ")",
            name="ck_bird_loss_valid_disposal",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'REVERSED')",
            name="ck_bird_loss_valid_status",
        ),
        CheckConstraint(
            "("
            "status = 'ACTIVE' "
            "AND reversal_population_transaction_id IS NULL "
            "AND reversed_by IS NULL "
            "AND reversed_at IS NULL "
            "AND reversal_reason IS NULL"
            ") OR ("
            "status = 'REVERSED' "
            "AND reversal_population_transaction_id "
            "IS NOT NULL "
            "AND reversed_by IS NOT NULL "
            "AND reversed_at IS NOT NULL "
            "AND reversal_reason IS NOT NULL"
            ")",
            name="ck_bird_loss_reversal_fields",
        ),
        UniqueConstraint(
            "population_transaction_id",
            name=("uq_bird_loss_population_transaction"),
        ),
        UniqueConstraint(
            "reversal_population_transaction_id",
            name=("uq_bird_loss_reversal_population_transaction"),
        ),
        Index(
            "ix_bird_loss_farm_date",
            "farm_id",
            "loss_date",
        ),
        Index(
            "ix_bird_loss_flock_date",
            "flock_id",
            "loss_date",
        ),
        Index(
            "ix_bird_loss_farm_type_date",
            "farm_id",
            "loss_type",
            "loss_date",
        ),
        Index(
            "ix_bird_loss_farm_status",
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

    loss_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    loss_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reason_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=BirdLossReason.UNKNOWN.value,
        server_default=BirdLossReason.UNKNOWN.value,
        index=True,
    )

    cause_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    disposal_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=BirdDisposalMethod.NOT_RECORDED.value,
        server_default=(BirdDisposalMethod.NOT_RECORDED.value),
    )

    disposal_details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    population_before: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    population_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    loss_percentage: Mapped[Decimal] = mapped_column(
        Numeric(7, 4),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=BirdLossRecordStatus.ACTIVE.value,
        server_default=BirdLossRecordStatus.ACTIVE.value,
        index=True,
    )

    population_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flock_population_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    reversal_population_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flock_population_transactions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
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

    reversed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    reversed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reversal_reason: Mapped[str | None] = mapped_column(
        Text,
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

    population_transaction: Mapped[FlockPopulationTransaction] = relationship(
        foreign_keys=[population_transaction_id],
        lazy="selectin",
    )

    reversal_population_transaction: Mapped[FlockPopulationTransaction | None] = (
        relationship(
            foreign_keys=[reversal_population_transaction_id],
            lazy="selectin",
        )
    )

    @property
    def is_reversed(self) -> bool:
        """Return whether this record has been reversed."""

        return self.status == BirdLossRecordStatus.REVERSED.value

    @property
    def is_mortality(self) -> bool:
        """Return whether this is a mortality record."""

        return self.loss_type == BirdLossType.MORTALITY.value

    @property
    def is_culling(self) -> bool:
        """Return whether this is a culling record."""

        return self.loss_type == BirdLossType.CULLING.value

    def __repr__(self) -> str:
        return (
            "BirdLossRecord("
            f"id={self.id!r}, "
            f"flock_id={self.flock_id!r}, "
            f"loss_type={self.loss_type!r}, "
            f"quantity={self.quantity!r}, "
            f"status={self.status!r}"
            ")"
        )


def calculate_population_after(
    population_before: int,
    quantity: int,
) -> int:
    """Calculate the population remaining after a loss."""

    if population_before <= 0:
        raise ValueError("Population before the loss must be positive.")

    if quantity <= 0:
        raise ValueError("Bird-loss quantity must be positive.")

    if quantity > population_before:
        raise ValueError("Bird-loss quantity cannot exceed the current population.")

    return population_before - quantity


def calculate_bird_loss_percentage(
    quantity: int,
    population_before: int,
) -> Decimal:
    """Calculate the loss as a percentage of population."""

    calculate_population_after(
        population_before,
        quantity,
    )

    percentage = Decimal(quantity) / Decimal(population_before) * Decimal("100")

    return percentage.quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_UP,
    )
