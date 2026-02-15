"""Add projection_status table for rebuild bookkeeping.

Revision ID: e2a7b9c4d0f1
Revises: d1f0a9b3c2e4
Create Date: 2026-02-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e2a7b9c4d0f1"
down_revision = "d1f0a9b3c2e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projection_status",
        sa.Column("projection_name", sa.String(length=100), primary_key=True, nullable=False),
        sa.Column("last_rebuild_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rebuild_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_rebuild_duration_seconds", sa.Float(), nullable=True),
        sa.Column("last_rebuild_success", sa.Boolean(), nullable=True),
        sa.Column("last_rebuild_error", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("timezone('utc', now())"),
        ),
    )


def downgrade() -> None:
    op.drop_table("projection_status")
