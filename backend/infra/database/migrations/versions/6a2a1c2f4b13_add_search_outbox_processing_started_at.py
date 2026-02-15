"""Add processing_started_at to search_outbox_events.

Revision ID: 6a2a1c2f4b13
Revises: e2a7b9c4d0f1
Create Date: 2026-02-02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a2a1c2f4b13"
down_revision = "e2a7b9c4d0f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "search_outbox_events",
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Backfill: for rows already in processing, approximate start time from updated_at.
    # This avoids immediately reclaiming older inflight rows right after deploying.
    op.execute(
        """
        UPDATE search_outbox_events
        SET processing_started_at = COALESCE(updated_at, created_at, timezone('utc', now()))
        WHERE status = 'processing' AND processing_started_at IS NULL;
        """
    )

    op.create_index(
        "idx_search_outbox_processing_started",
        "search_outbox_events",
        ["status", "processing_started_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_search_outbox_processing_started", table_name="search_outbox_events")
    op.drop_column("search_outbox_events", "processing_started_at")
