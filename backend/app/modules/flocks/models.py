from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

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
from app.modules.farms.models import Farm
from app.modules.flocks.constants import (
    FlockProductionStage,
    FlockStatus,
    PopulationTransactionType,
)
from app.modules.houses.models import PoultryHouse
from app.modules.suppliers.models import Supplier


class Flock(Base):
    """Represents a group or batch of poultry birds."""

    __tablename__ = "flocks"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "flock_code",
            name="uq_flocks_farm_code",
        ),
        CheckConstraint(
            "initial_population > 0",
            name="ck_flocks_initial_population_positive",
        ),
        CheckConstraint(
            "age_at_arrival_days IS NULL OR age_at_arrival_days >= 0",
            name="ck_flocks_age_at_arrival_nonnegative",
        ),
        CheckConstraint(
            "purchase_cost >= 0",
            name="ck_flocks_purchase_cost_nonnegative",
        ),
        CheckConstraint(
            "hatch_date IS NULL OR hatch_date <= arrival_date",
            name="ck_flocks_hatch_before_arrival",
        ),
        CheckConstraint(
            "production_stage IN ("
            "'BROODING', "
            "'GROWING', "
            "'POINT_OF_LAY', "
            "'LAYING', "
            "'MOLTING', "
            "'DEPLETED', "
            "'SOLD'"
            ")",
            name="ck_flocks_valid_production_stage",
        ),
        CheckConstraint(
            "status IN ("
            "'PLANNED', "
            "'ACTIVE', "
            "'SUSPENDED', "
            "'DEPLETED', "
            "'SOLD', "
            "'ARCHIVED'"
            ")",
            name="ck_flocks_valid_status",
        ),
        Index(
            "ix_flocks_farm_house_status",
            "farm_id",
            "house_id",
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
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    house_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "poultry_houses.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    supplier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "suppliers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    flock_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    breed: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    arrival_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    hatch_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    age_at_arrival_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    initial_population: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    purchase_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    production_stage: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FlockProductionStage.GROWING.value,
        server_default=FlockProductionStage.GROWING.value,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FlockStatus.ACTIVE.value,
        server_default=FlockStatus.ACTIVE.value,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
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

    house: Mapped[PoultryHouse] = relationship(
        lazy="selectin",
    )

    supplier: Mapped[Supplier | None] = relationship(
        lazy="selectin",
    )

    population_transactions: Mapped[list[FlockPopulationTransaction]] = relationship(
        back_populates="flock",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"Flock(id={self.id!r}, flock_code={self.flock_code!r}, name={self.name!r})"
        )


class FlockPopulationTransaction(Base):
    """Records one auditable change to a flock population."""

    __tablename__ = "flock_population_transactions"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name=("ck_flock_population_transactions_quantity_positive"),
        ),
        CheckConstraint(
            "signed_quantity <> 0",
            name=("ck_flock_population_transactions_signed_quantity_nonzero"),
        ),
        CheckConstraint(
            "transaction_type IN ("
            "'INITIAL_PLACEMENT', "
            "'TRANSFER_IN', "
            "'TRANSFER_OUT', "
            "'MORTALITY', "
            "'CULLING', "
            "'BIRD_SALE', "
            "'ADJUSTMENT_IN', "
            "'ADJUSTMENT_OUT', "
            "'REVERSAL'"
            ")",
            name=("ck_flock_population_transactions_valid_type"),
        ),
        Index(
            "ix_flock_population_transactions_flock_date",
            "flock_id",
            "transaction_date",
        ),
        Index(
            "ix_flock_population_transactions_source",
            "source_type",
            "source_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    flock_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("flocks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    signed_quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    reversed_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "flock_population_transactions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    flock: Mapped[Flock] = relationship(
        back_populates="population_transactions",
        foreign_keys=[flock_id],
    )

    def __repr__(self) -> str:
        return (
            "FlockPopulationTransaction("
            f"id={self.id!r}, "
            f"transaction_type={self.transaction_type!r}, "
            f"signed_quantity={self.signed_quantity!r}"
            ")"
        )


POSITIVE_POPULATION_TRANSACTION_TYPES = {
    PopulationTransactionType.INITIAL_PLACEMENT.value,
    PopulationTransactionType.TRANSFER_IN.value,
    PopulationTransactionType.ADJUSTMENT_IN.value,
}


NEGATIVE_POPULATION_TRANSACTION_TYPES = {
    PopulationTransactionType.TRANSFER_OUT.value,
    PopulationTransactionType.MORTALITY.value,
    PopulationTransactionType.CULLING.value,
    PopulationTransactionType.BIRD_SALE.value,
    PopulationTransactionType.ADJUSTMENT_OUT.value,
}
