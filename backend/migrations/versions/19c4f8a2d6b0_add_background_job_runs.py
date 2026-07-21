"""Add background job run history.

Revision ID: 19c4f8a2d6b0
Revises: 4ace107b803e
Create Date: 2026-07-21
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "19c4f8a2d6b0"
down_revision: str | Sequence[str] | None = "4ace107b803e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "background_job_runs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "farm_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "job_name",
            sa.String(length=80),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "trigger",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "scheduled_for",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "result_json",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "error_type",
            sa.String(length=120),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "worker_id",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["farm_id"],
            ["farms.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_background_job_runs_job_started",
        "background_job_runs",
        ["job_name", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_background_job_runs_farm_started",
        "background_job_runs",
        ["farm_id", "started_at"],
        unique=False,
    )
    op.create_index(
        "ix_background_job_runs_status_started",
        "background_job_runs",
        ["status", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_background_job_runs_status_started",
        table_name="background_job_runs",
    )
    op.drop_index(
        "ix_background_job_runs_farm_started",
        table_name="background_job_runs",
    )
    op.drop_index(
        "ix_background_job_runs_job_started",
        table_name="background_job_runs",
    )
    op.drop_table("background_job_runs")
