"""Add platform-controlled farm lifecycle state.

Revision ID: a84f1d2c9b73
Revises: 7b1a6d4f2c90
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "a84f1d2c9b73"
down_revision: str | None = "7b1a6d4f2c90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "farms",
        sa.Column(
            "lifecycle_status",
            sa.String(length=20),
            server_default="ACTIVE",
            nullable=False,
        ),
    )
    op.add_column(
        "farms",
        sa.Column(
            "lifecycle_reason",
            sa.Text(),
            nullable=True,
        ),
    )
    op.add_column(
        "farms",
        sa.Column(
            "lifecycle_changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "farms",
        sa.Column(
            "lifecycle_changed_by_platform_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "farms",
        sa.Column(
            "suspended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "farms",
        sa.Column(
            "deactivated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.execute(
        sa.text(
            """
            UPDATE farms
            SET
                lifecycle_status = CASE
                    WHEN is_active THEN 'ACTIVE'
                    ELSE 'DEACTIVATED'
                END,
                lifecycle_reason = CASE
                    WHEN is_active THEN NULL
                    ELSE 'Migrated from the legacy inactive state.'
                END,
                lifecycle_changed_at = COALESCE(
                    updated_at,
                    created_at,
                    NOW()
                ),
                deactivated_at = CASE
                    WHEN is_active THEN NULL
                    ELSE COALESCE(updated_at, created_at, NOW())
                END
            """
        )
    )

    op.create_foreign_key(
        "fk_farms_lifecycle_platform_user",
        "farms",
        "platform_users",
        ["lifecycle_changed_by_platform_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_farms_lifecycle_status",
        "farms",
        ["lifecycle_status"],
        unique=False,
    )
    op.create_index(
        "ix_farms_lifecycle_changed_by_platform_user_id",
        "farms",
        ["lifecycle_changed_by_platform_user_id"],
        unique=False,
    )
    op.create_check_constraint(
        "ck_farms_lifecycle_status_valid",
        "farms",
        (
            "lifecycle_status IN "
            "('ACTIVE', 'SUSPENDED', 'DEACTIVATED')"
        ),
    )
    op.create_check_constraint(
        "ck_farms_lifecycle_active_consistency",
        "farms",
        (
            "(lifecycle_status = 'ACTIVE' AND is_active = TRUE) "
            "OR "
            "(lifecycle_status IN ('SUSPENDED', 'DEACTIVATED') "
            "AND is_active = FALSE)"
        ),
    )
    op.create_check_constraint(
        "ck_farms_lifecycle_reason_required",
        "farms",
        (
            "lifecycle_status = 'ACTIVE' "
            "OR "
            "(lifecycle_reason IS NOT NULL "
            "AND length(trim(lifecycle_reason)) >= 5)"
        ),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_farms_lifecycle_reason_required",
        "farms",
        type_="check",
    )
    op.drop_constraint(
        "ck_farms_lifecycle_active_consistency",
        "farms",
        type_="check",
    )
    op.drop_constraint(
        "ck_farms_lifecycle_status_valid",
        "farms",
        type_="check",
    )
    op.drop_index(
        "ix_farms_lifecycle_changed_by_platform_user_id",
        table_name="farms",
    )
    op.drop_index(
        "ix_farms_lifecycle_status",
        table_name="farms",
    )
    op.drop_constraint(
        "fk_farms_lifecycle_platform_user",
        "farms",
        type_="foreignkey",
    )
    op.drop_column("farms", "deactivated_at")
    op.drop_column("farms", "suspended_at")
    op.drop_column(
        "farms",
        "lifecycle_changed_by_platform_user_id",
    )
    op.drop_column(
        "farms",
        "lifecycle_changed_at",
    )
    op.drop_column("farms", "lifecycle_reason")
    op.drop_column("farms", "lifecycle_status")
