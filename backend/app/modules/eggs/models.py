from __future__ import annotations

import uuid
from datetime import date, datetime

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
from app.modules.eggs.constants import (
    EggGrade,
    EggInventoryTransactionType,
    NEGATIVE_EGG_TRANSACTION_TYPES,
    POSITIVE_EGG_TRANSACTION_TYPES,
)
from app.modules.farms.models import Farm


class EggInventoryTransaction(Base):
    """Represents one auditable egg-stock movement."""

    __tablename__ = "egg_inventory_transactions"

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="ck_egg_inventory_quantity_positive",
        ),
        CheckConstraint(
            "signed_quantity <> 0",
            name="ck_egg_inventory_signed_nonzero",
        ),
        CheckConstraint(
            "egg_grade IN ('LARGE', 'MEDIUM', 'SMALL', 'DAMAGED', 'REJECTED')",
            name="ck_egg_inventory_valid_grade",
        ),
        CheckConstraint(
            "transaction_type IN ("
            "'PRODUCTION_IN', "
            "'SALE_OUT', "
            "'SALE_RETURN_IN', "
            "'INTERNAL_USE_OUT', "
            "'DONATION_OUT', "
            "'DAMAGE_OUT', "
            "'ADJUSTMENT_IN', "
            "'ADJUSTMENT_OUT', "
            "'REVERSAL'"
            ")",
            name="ck_egg_inventory_valid_type",
        ),
        CheckConstraint(
            "("
            "transaction_type = 'REVERSAL'"
            ") OR ("
            "transaction_type IN ("
            "'PRODUCTION_IN', "
            "'SALE_RETURN_IN', "
            "'ADJUSTMENT_IN'"
            ") AND signed_quantity > 0"
            ") OR ("
            "transaction_type IN ("
            "'SALE_OUT', "
            "'INTERNAL_USE_OUT', "
            "'DONATION_OUT', "
            "'DAMAGE_OUT', "
            "'ADJUSTMENT_OUT'"
            ") AND signed_quantity < 0"
            ")",
            name="ck_egg_inventory_sign_matches_type",
        ),
        UniqueConstraint(
            "farm_id",
            "source_type",
            "source_id",
            "egg_grade",
            "transaction_type",
            name="uq_egg_inventory_source_grade_type",
        ),
        Index(
            "ix_egg_inventory_farm_grade_date",
            "farm_id",
            "egg_grade",
            "inventory_date",
        ),
        Index(
            "ix_egg_inventory_farm_type_date",
            "farm_id",
            "transaction_type",
            "inventory_date",
        ),
        Index(
            "ix_egg_inventory_source",
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
        ForeignKey(
            "farms.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    transaction_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        default=uuid.uuid4,
        index=True,
    )

    inventory_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    egg_grade: Mapped[str] = mapped_column(
        String(30),
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
        String(60),
        nullable=False,
    )

    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    reversed_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "egg_inventory_transactions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    farm: Mapped[Farm] = relationship(
        lazy="selectin",
    )

    reversed_transaction: Mapped[EggInventoryTransaction | None] = relationship(
        remote_side=lambda: EggInventoryTransaction.id,
        foreign_keys=[reversed_transaction_id],
        lazy="selectin",
    )

    @property
    def direction(self) -> str:
        """Return whether the transaction adds or removes stock."""

        if self.signed_quantity > 0:
            return "IN"

        return "OUT"

    @property
    def is_reversal(self) -> bool:
        """Return whether this transaction reverses another."""

        return self.transaction_type == EggInventoryTransactionType.REVERSAL.value

    def __repr__(self) -> str:
        return (
            "EggInventoryTransaction("
            f"id={self.id!r}, "
            f"egg_grade={self.egg_grade!r}, "
            f"transaction_type={self.transaction_type!r}, "
            f"signed_quantity={self.signed_quantity!r}"
            ")"
        )


def get_signed_egg_quantity(
    transaction_type: str,
    quantity: int,
) -> int:
    """Convert a positive quantity into its ledger direction."""

    if transaction_type in POSITIVE_EGG_TRANSACTION_TYPES:
        return quantity

    if transaction_type in NEGATIVE_EGG_TRANSACTION_TYPES:
        return -quantity

    raise ValueError("The transaction type requires an explicit reversal quantity.")


def validate_egg_grade(egg_grade: str) -> str:
    """Validate a raw egg-grade value."""

    valid_grades = {grade.value for grade in EggGrade}

    if egg_grade not in valid_grades:
        raise ValueError(f"Unsupported egg grade: {egg_grade!r}.")

    return egg_grade
