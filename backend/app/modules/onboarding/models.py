from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
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
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.modules.onboarding.constants import (
    FarmInvitationDeliveryStatus,
    FarmInvitationStatus,
)


class PlatformFarmInvitation(Base):
    """Stores one hashed, expiring farm-administrator setup invitation."""

    __tablename__ = "platform_farm_invitations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')",
            name="ck_platform_farm_invitations_status_valid",
        ),
        CheckConstraint(
            "delivery_status IN "
            "('NOT_CONFIGURED', 'PENDING', 'SENT', 'FAILED')",
            name="ck_platform_farm_invitations_delivery_status_valid",
        ),
        CheckConstraint(
            "delivery_attempt_count >= 0",
            name="ck_platform_farm_invitations_attempts_nonnegative",
        ),
        CheckConstraint(
            "length(token_hash) = 64",
            name="ck_platform_farm_invitations_token_hash_length",
        ),
        CheckConstraint(
            "status != 'ACCEPTED' OR accepted_at IS NOT NULL",
            name="ck_platform_farm_invitations_accepted_consistency",
        ),
        UniqueConstraint(
            "issued_by_platform_user_id",
            "idempotency_key",
            name="uq_platform_farm_invitations_actor_idempotency",
        ),
        Index(
            "ix_platform_farm_invitations_farm_created",
            "farm_id",
            "created_at",
        ),
        Index(
            "ix_platform_farm_invitations_status_expires",
            "status",
            "expires_at",
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
    administrator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issued_by_platform_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("platform_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=FarmInvitationStatus.PENDING.value,
        server_default=FarmInvitationStatus.PENDING.value,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    delivery_status: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        default=FarmInvitationDeliveryStatus.NOT_CONFIGURED.value,
        server_default=FarmInvitationDeliveryStatus.NOT_CONFIGURED.value,
        index=True,
    )
    delivery_attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_delivery_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_delivery_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    request_fingerprint: Mapped[str | None] = mapped_column(
        String(64),
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
