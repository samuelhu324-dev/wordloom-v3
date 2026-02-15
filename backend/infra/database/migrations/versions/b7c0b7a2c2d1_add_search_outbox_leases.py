"""Add lease/claim fields to search_outbox_events

Revision ID: b7c0b7a2c2d1
Revises: 4f2c9a11a8aa
Create Date: 2026-02-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c0b7a2c2d1"
down_revision: Union[str, Sequence[str], None] = "4f2c9a11a8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "search_outbox_events",
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
    )
    op.add_column(
        "search_outbox_events",
        sa.Column("owner", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "search_outbox_events",
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "search_outbox_events",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "search_outbox_events",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "search_outbox_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # Backfill status/updated_at for existing rows.
    op.execute(
        """
        UPDATE search_outbox_events
        SET
          status = CASE WHEN processed_at IS NULL THEN 'pending' ELSE 'done' END,
          updated_at = COALESCE(processed_at, created_at, CURRENT_TIMESTAMP),
          attempts = COALESCE(attempts, 0)
        """
    )

    op.create_index("ix_search_outbox_events_status", "search_outbox_events", ["status"], unique=False)
    op.create_index("ix_search_outbox_events_owner", "search_outbox_events", ["owner"], unique=False)
    op.create_index("ix_search_outbox_events_lease_until", "search_outbox_events", ["lease_until"], unique=False)
    op.create_index("ix_search_outbox_events_next_retry_at", "search_outbox_events", ["next_retry_at"], unique=False)

    # Claiming index for SKIP LOCKED pick + retry gating.
    op.create_index(
        "idx_search_outbox_claim",
        "search_outbox_events",
        ["status", "next_retry_at", "lease_until", "event_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_search_outbox_claim", table_name="search_outbox_events")
    op.drop_index("ix_search_outbox_events_next_retry_at", table_name="search_outbox_events")
    op.drop_index("ix_search_outbox_events_lease_until", table_name="search_outbox_events")
    op.drop_index("ix_search_outbox_events_owner", table_name="search_outbox_events")
    op.drop_index("ix_search_outbox_events_status", table_name="search_outbox_events")

    op.drop_column("search_outbox_events", "updated_at")
    op.drop_column("search_outbox_events", "next_retry_at")
    op.drop_column("search_outbox_events", "attempts")
    op.drop_column("search_outbox_events", "lease_until")
    op.drop_column("search_outbox_events", "owner")
    op.drop_column("search_outbox_events", "status")
