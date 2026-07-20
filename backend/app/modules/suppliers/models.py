from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.modules.farms.models import Farm
from app.modules.suppliers.constants import SupplierType


class Supplier(Base):
    """Represents a supplier serving a PoultryPulse farm."""

    __tablename__ = "suppliers"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "supplier_code",
            name="uq_suppliers_farm_code",
        ),
        CheckConstraint(
            "supplier_type IN ("
            "'BIRD_SUPPLIER', "
            "'FEED_SUPPLIER', "
            "'MEDICINE_SUPPLIER', "
            "'EQUIPMENT_SUPPLIER', "
            "'GENERAL_SUPPLIER'"
            ")",
            name="ck_suppliers_valid_type",
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

    supplier_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    supplier_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=SupplierType.GENERAL_SUPPLIER.value,
        server_default=SupplierType.GENERAL_SUPPLIER.value,
        index=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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
            "Supplier("
            f"id={self.id!r}, "
            f"supplier_code={self.supplier_code!r}, "
            f"name={self.name!r}"
            ")"
        )
