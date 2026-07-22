"""Add secure farm administrator onboarding invitations.

Revision ID: d13f7b9c4e21
Revises: a84f1d2c9b73
Create Date: 2026-07-22
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "d13f7b9c4e21"
down_revision: str | None = "a84f1d2c9b73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the platform farm-invitation table."""

    op.create_table(
        "platform_farm_invitations",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "farm_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "administrator_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "issued_by_platform_user_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="PENDING",
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "delivery_status",
            sa.String(length=24),
            server_default="NOT_CONFIGURED",
            nullable=False,
        ),
        sa.Column(
            "delivery_attempt_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "last_delivery_attempt_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_delivery_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=128),
            nullable=True,
        ),
        sa.Column(
            "request_fingerprint",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')",
            name="ck_platform_farm_invitations_status_valid",
        ),
        sa.CheckConstraint(
            "delivery_status IN "
            "('NOT_CONFIGURED', 'PENDING', 'SENT', 'FAILED')",
            name=(
                "ck_platform_farm_invitations_delivery_status_valid"
            ),
        ),
        sa.CheckConstraint(
            "delivery_attempt_count >= 0",
            name=(
                "ck_platform_farm_invitations_attempts_nonnegative"
            ),
        ),
        sa.CheckConstraint(
            "length(token_hash) = 64",
            name=(
                "ck_platform_farm_invitations_token_hash_length"
            ),
        ),
        sa.CheckConstraint(
            "status != 'ACCEPTED' OR accepted_at IS NOT NULL",
            name=(
                "ck_platform_farm_invitations_accepted_consistency"
            ),
        ),
        sa.ForeignKeyConstraint(
            ["administrator_user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"],
            ["farms.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["issued_by_platform_user_id"],
            ["platform_users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "issued_by_platform_user_id",
            "idempotency_key",
            name=(
                "uq_platform_farm_invitations_actor_idempotency"
            ),
        ),
    )
    op.create_index(
        "ix_platform_farm_invitations_administrator_user_id",
        "platform_farm_invitations",
        ["administrator_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_delivery_status",
        "platform_farm_invitations",
        ["delivery_status"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_farm_created",
        "platform_farm_invitations",
        ["farm_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_farm_id",
        "platform_farm_invitations",
        ["farm_id"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_issued_by_platform_user_id",
        "platform_farm_invitations",
        ["issued_by_platform_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_status",
        "platform_farm_invitations",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_status_expires",
        "platform_farm_invitations",
        ["status", "expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_expires_at",
        "platform_farm_invitations",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_platform_farm_invitations_token_hash",
        "platform_farm_invitations",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Remove secure farm administrator onboarding invitations."""

    op.drop_index(
        "ix_platform_farm_invitations_token_hash",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_expires_at",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_status_expires",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_status",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_issued_by_platform_user_id",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_farm_id",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_farm_created",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_delivery_status",
        table_name="platform_farm_invitations",
    )
    op.drop_index(
        "ix_platform_farm_invitations_administrator_user_id",
        table_name="platform_farm_invitations",
    )
    op.drop_table("platform_farm_invitations")
