"""Add error_reason + manual replay audit fields to search_outbox_events.

Revision ID: 0f3c2a7d9b41
Revises: 6a2a1c2f4b13
Create Date: 2026-02-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0f3c2a7d9b41"
down_revision = "6a2a1c2f4b13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("search_outbox_events", sa.Column("error_reason", sa.String(length=80), nullable=True))

    op.add_column(
        "search_outbox_events",
        sa.Column("replay_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("search_outbox_events", sa.Column("last_replayed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("search_outbox_events", sa.Column("last_replayed_by", sa.String(length=120), nullable=True))
    op.add_column("search_outbox_events", sa.Column("last_replayed_reason", sa.Text(), nullable=True))

    # Drop server default to keep model-level default behavior.
    op.alter_column("search_outbox_events", "replay_count", server_default=None)

    op.create_index(
        "idx_search_outbox_error_reason",
        "search_outbox_events",
        ["status", "error_reason"],
    )


def downgrade() -> None:
    op.drop_index("idx_search_outbox_error_reason", table_name="search_outbox_events")

    op.drop_column("search_outbox_events", "last_replayed_reason")
    op.drop_column("search_outbox_events", "last_replayed_by")
    op.drop_column("search_outbox_events", "last_replayed_at")
    op.drop_column("search_outbox_events", "replay_count")

    op.drop_column("search_outbox_events", "error_reason")
