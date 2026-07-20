from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
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
from app.modules.feed.constants import (
    FeedCategory,
    FeedInventoryTransactionType,
    FeedPurchaseStatus,
    FeedUsagePeriod,
    NEGATIVE_FEED_TRANSACTION_TYPES,
    POSITIVE_FEED_TRANSACTION_TYPES,
)
from app.modules.flocks.models import Flock
from app.modules.suppliers.models import Supplier


class FeedItem(Base):
    """Represents one type of feed stocked by a farm."""

    __tablename__ = "feed_items"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "feed_code",
            name="uq_feed_items_farm_code",
        ),
        CheckConstraint(
            "reorder_level_kg >= 0",
            name="ck_feed_items_reorder_level_nonnegative",
        ),
        CheckConstraint(
            "category IN ("
            "'CHICK_STARTER', "
            "'GROWERS_MASH', "
            "'LAYERS_MASH', "
            "'BROILER_STARTER', "
            "'BROILER_FINISHER', "
            "'CONCENTRATE', "
            "'SUPPLEMENT', "
            "'OTHER'"
            ")",
            name="ck_feed_items_valid_category",
        ),
        Index(
            "ix_feed_items_farm_category",
            "farm_id",
            "category",
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

    feed_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default=FeedCategory.OTHER.value,
        server_default=FeedCategory.OTHER.value,
        index=True,
    )

    brand: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reorder_level_kg: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
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

    def __repr__(self) -> str:
        return (
            "FeedItem("
            f"id={self.id!r}, "
            f"feed_code={self.feed_code!r}, "
            f"name={self.name!r}"
            ")"
        )


class FeedPurchase(Base):
    """Represents feed received from a supplier."""

    __tablename__ = "feed_purchases"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "supplier_id",
            "invoice_number",
            "feed_item_id",
            name="uq_feed_purchases_supplier_invoice_item",
        ),
        CheckConstraint(
            "quantity_kg > 0",
            name="ck_feed_purchases_quantity_positive",
        ),
        CheckConstraint(
            "unit_cost >= 0",
            name="ck_feed_purchases_unit_cost_nonnegative",
        ),
        CheckConstraint(
            "status IN ('RECEIVED', 'VOIDED')",
            name="ck_feed_purchases_valid_status",
        ),
        Index(
            "ix_feed_purchases_farm_date",
            "farm_id",
            "purchase_date",
        ),
        Index(
            "ix_feed_purchases_item_date",
            "feed_item_id",
            "purchase_date",
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

    feed_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "feed_items.id",
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

    purchase_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    quantity_kg: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeedPurchaseStatus.RECEIVED.value,
        server_default=FeedPurchaseStatus.RECEIVED.value,
        index=True,
    )

    notes: Mapped[str | None] = mapped_column(
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

    feed_item: Mapped[FeedItem] = relationship(
        lazy="selectin",
    )

    supplier: Mapped[Supplier | None] = relationship(
        lazy="selectin",
    )

    @property
    def total_cost(self) -> Decimal:
        """Return the total cost of the purchase."""

        total = self.quantity_kg * self.unit_cost

        return total.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    def __repr__(self) -> str:
        return (
            "FeedPurchase("
            f"id={self.id!r}, "
            f"feed_item_id={self.feed_item_id!r}, "
            f"quantity_kg={self.quantity_kg!r}"
            ")"
        )


class FeedUsage(Base):
    """Represents feed issued to and consumed by a flock."""

    __tablename__ = "feed_usages"

    __table_args__ = (
        CheckConstraint(
            "quantity_kg > 0",
            name="ck_feed_usages_quantity_positive",
        ),
        CheckConstraint(
            "feeding_period IN ('MORNING', 'AFTERNOON', 'EVENING', 'OTHER')",
            name="ck_feed_usages_valid_period",
        ),
        Index(
            "ix_feed_usages_farm_date",
            "farm_id",
            "usage_date",
        ),
        Index(
            "ix_feed_usages_flock_date",
            "flock_id",
            "usage_date",
        ),
        Index(
            "ix_feed_usages_item_date",
            "feed_item_id",
            "usage_date",
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

    feed_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "feed_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    usage_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    feeding_period: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=FeedUsagePeriod.OTHER.value,
        server_default=FeedUsagePeriod.OTHER.value,
        index=True,
    )

    quantity_kg: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    flock: Mapped[Flock] = relationship(
        lazy="selectin",
    )

    feed_item: Mapped[FeedItem] = relationship(
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            "FeedUsage("
            f"id={self.id!r}, "
            f"flock_id={self.flock_id!r}, "
            f"quantity_kg={self.quantity_kg!r}"
            ")"
        )


class FeedInventoryTransaction(Base):
    """Represents one auditable feed-stock movement."""

    __tablename__ = "feed_inventory_transactions"

    __table_args__ = (
        CheckConstraint(
            "quantity_kg > 0",
            name="ck_feed_inventory_quantity_positive",
        ),
        CheckConstraint(
            "signed_quantity_kg <> 0",
            name="ck_feed_inventory_signed_nonzero",
        ),
        CheckConstraint(
            "transaction_type IN ("
            "'PURCHASE_IN', "
            "'RETURN_IN', "
            "'USAGE_OUT', "
            "'WASTAGE_OUT', "
            "'SUPPLIER_RETURN_OUT', "
            "'ADJUSTMENT_IN', "
            "'ADJUSTMENT_OUT', "
            "'REVERSAL'"
            ")",
            name="ck_feed_inventory_valid_type",
        ),
        CheckConstraint(
            "("
            "transaction_type = 'REVERSAL'"
            ") OR ("
            "transaction_type IN ("
            "'PURCHASE_IN', "
            "'RETURN_IN', "
            "'ADJUSTMENT_IN'"
            ") AND signed_quantity_kg > 0"
            ") OR ("
            "transaction_type IN ("
            "'USAGE_OUT', "
            "'WASTAGE_OUT', "
            "'SUPPLIER_RETURN_OUT', "
            "'ADJUSTMENT_OUT'"
            ") AND signed_quantity_kg < 0"
            ")",
            name="ck_feed_inventory_sign_matches_type",
        ),
        UniqueConstraint(
            "farm_id",
            "source_type",
            "source_id",
            "transaction_type",
            name="uq_feed_inventory_source_type",
        ),
        Index(
            "ix_feed_inventory_farm_item_date",
            "farm_id",
            "feed_item_id",
            "inventory_date",
        ),
        Index(
            "ix_feed_inventory_farm_type_date",
            "farm_id",
            "transaction_type",
            "inventory_date",
        ),
        Index(
            "ix_feed_inventory_source",
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

    feed_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "feed_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    inventory_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        index=True,
    )

    quantity_kg: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
        nullable=False,
    )

    signed_quantity_kg: Mapped[Decimal] = mapped_column(
        Numeric(14, 3),
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
            "feed_inventory_transactions.id",
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

    feed_item: Mapped[FeedItem] = relationship(
        lazy="selectin",
    )

    reversed_transaction: Mapped[FeedInventoryTransaction | None] = relationship(
        remote_side=lambda: FeedInventoryTransaction.id,
        foreign_keys=[reversed_transaction_id],
        lazy="selectin",
    )

    @property
    def direction(self) -> str:
        """Return the stock direction of the transaction."""

        if self.signed_quantity_kg > 0:
            return "IN"

        return "OUT"

    @property
    def is_reversal(self) -> bool:
        """Return whether the transaction is a reversal."""

        return self.transaction_type == FeedInventoryTransactionType.REVERSAL.value

    def __repr__(self) -> str:
        return (
            "FeedInventoryTransaction("
            f"id={self.id!r}, "
            f"feed_item_id={self.feed_item_id!r}, "
            f"transaction_type={self.transaction_type!r}, "
            f"signed_quantity_kg="
            f"{self.signed_quantity_kg!r}"
            ")"
        )


def get_signed_feed_quantity(
    transaction_type: str,
    quantity_kg: Decimal,
) -> Decimal:
    """Apply the correct ledger direction to feed quantity."""

    if transaction_type in POSITIVE_FEED_TRANSACTION_TYPES:
        return quantity_kg

    if transaction_type in NEGATIVE_FEED_TRANSACTION_TYPES:
        return -quantity_kg

    raise ValueError("The transaction type requires an explicit reversal quantity.")
