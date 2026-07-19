from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Farm(Base):
    """Represents a poultry farm registered in PoultryPulse."""

    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    farm_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    owner_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    telephone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    district: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Africa/Kampala",
        server_default="Africa/Kampala",
    )

    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="UGX",
        server_default="UGX",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    settings: Mapped[FarmSettings | None] = relationship(
        back_populates="farm",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Farm(id={self.id!r}, code={self.farm_code!r}, name={self.name!r})"


class FarmSettings(Base):
    """Stores configurable settings for one farm."""

    __tablename__ = "farm_settings"

    __table_args__ = (
        CheckConstraint(
            "eggs_per_tray > 0",
            name="ck_farm_settings_eggs_per_tray_positive",
        ),
        CheckConstraint(
            "low_production_threshold >= 0 "
            "AND low_production_threshold <= 100",
            name="ck_farm_settings_low_production_percentage",
        ),
        CheckConstraint(
            "mortality_alert_threshold >= 0 "
            "AND mortality_alert_threshold <= 100",
            name="ck_farm_settings_mortality_percentage",
        ),
        CheckConstraint(
            "vaccination_reminder_days >= 0",
            name="ck_farm_settings_vaccination_days_nonnegative",
        ),
        CheckConstraint(
            "session_timeout_minutes > 0",
            name="ck_farm_settings_session_timeout_positive",
        ),
        CheckConstraint(
            "maximum_discount_percentage >= 0 "
            "AND maximum_discount_percentage <= 100",
            name="ck_farm_settings_discount_percentage",
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
        unique=True,
        index=True,
    )

    eggs_per_tray: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default="30",
    )

    low_production_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("70.00"),
        server_default="70.00",
    )

    mortality_alert_threshold: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("1.00"),
        server_default="1.00",
    )

    vaccination_reminder_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        server_default="3",
    )

    session_timeout_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        server_default="60",
    )

    allow_negative_stock: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    allow_customer_credit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    maximum_discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
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
        back_populates="settings",
    )

    def __repr__(self) -> str:
        return (
            "FarmSettings("
            f"id={self.id!r}, "
            f"farm_id={self.farm_id!r}, "
            f"eggs_per_tray={self.eggs_per_tray!r}"
            ")"
        )
