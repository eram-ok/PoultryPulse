from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
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
from app.modules.houses.constants import PoultryHouseStatus


class PoultryHouse(Base):
    """Represents a physical poultry house on a farm."""

    __tablename__ = "poultry_houses"

    __table_args__ = (
        UniqueConstraint(
            "farm_id",
            "house_code",
            name="uq_poultry_houses_farm_code",
        ),
        CheckConstraint(
            "capacity > 0",
            name="ck_poultry_houses_capacity_positive",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE', 'UNDER_MAINTENANCE', 'CLOSED')",
            name="ck_poultry_houses_valid_status",
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

    house_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=PoultryHouseStatus.ACTIVE.value,
        server_default=PoultryHouseStatus.ACTIVE.value,
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
            "PoultryHouse("
            f"id={self.id!r}, "
            f"house_code={self.house_code!r}, "
            f"name={self.name!r}"
            ")"
        )
