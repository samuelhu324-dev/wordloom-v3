"""Add chronicle_outbox_events + chronicle_entries.

Revision ID: 2d7f6a1c9b0e
Revises: 0f3c2a7d9b41
Create Date: 2026-02-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "2d7f6a1c9b0e"
down_revision = "0f3c2a7d9b41"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------------
    # chronicle_outbox_events (isomorphic to search_outbox_events)
    # ---------------------------------------------------------------------
    op.create_table(
        "chronicle_outbox_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("op", sa.String(length=20), nullable=False),
        sa.Column("event_version", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("owner", sa.String(length=120), nullable=True),
        sa.Column("lease_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processing_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_reason", sa.String(length=80), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("replay_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_replayed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_replayed_by", sa.String(length=120), nullable=True),
        sa.Column("last_replayed_reason", sa.Text(), nullable=True),
    )

    # Keep model-level defaults; drop server defaults where appropriate.
    op.alter_column("chronicle_outbox_events", "event_version", server_default=None)
    op.alter_column("chronicle_outbox_events", "attempts", server_default=None)
    op.alter_column("chronicle_outbox_events", "replay_count", server_default=None)

    op.create_index("ix_chronicle_outbox_events_status", "chronicle_outbox_events", ["status"], unique=False)
    op.create_index("ix_chronicle_outbox_events_owner", "chronicle_outbox_events", ["owner"], unique=False)
    op.create_index("ix_chronicle_outbox_events_lease_until", "chronicle_outbox_events", ["lease_until"], unique=False)
    op.create_index("ix_chronicle_outbox_events_next_retry_at", "chronicle_outbox_events", ["next_retry_at"], unique=False)
    op.create_index("ix_chronicle_outbox_events_event_version", "chronicle_outbox_events", ["event_version"], unique=False)
    op.create_index("ix_chronicle_outbox_events_entity_type", "chronicle_outbox_events", ["entity_type"], unique=False)
    op.create_index("ix_chronicle_outbox_events_entity_id", "chronicle_outbox_events", ["entity_id"], unique=False)
    op.create_index("ix_chronicle_outbox_events_processed_at", "chronicle_outbox_events", ["processed_at"], unique=False)
    op.create_index(
        "ix_chronicle_outbox_events_processing_started_at",
        "chronicle_outbox_events",
        ["processing_started_at"],
        unique=False,
    )
    op.create_index("ix_chronicle_outbox_events_error_reason", "chronicle_outbox_events", ["error_reason"], unique=False)

    op.create_index(
        "idx_chronicle_outbox_entity",
        "chronicle_outbox_events",
        ["entity_type", "entity_id"],
        unique=False,
    )
    op.create_index(
        "idx_chronicle_outbox_processed",
        "chronicle_outbox_events",
        ["processed_at"],
        unique=False,
    )
    op.create_index(
        "idx_chronicle_outbox_claim",
        "chronicle_outbox_events",
        ["status", "next_retry_at", "lease_until", "event_version"],
        unique=False,
    )
    op.create_index(
        "idx_chronicle_outbox_processing_started",
        "chronicle_outbox_events",
        ["status", "processing_started_at"],
        unique=False,
    )
    op.create_index(
        "idx_chronicle_outbox_error_reason",
        "chronicle_outbox_events",
        ["status", "error_reason"],
        unique=False,
    )

    # ---------------------------------------------------------------------
    # chronicle_entries (read-optimized projection)
    # ---------------------------------------------------------------------
    op.create_table(
        "chronicle_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("projection_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="SET NULL"),
    )

    op.alter_column("chronicle_entries", "projection_version", server_default=None)

    op.create_index("ix_chronicle_entries_event_type", "chronicle_entries", ["event_type"], unique=False)
    op.create_index("ix_chronicle_entries_book_id", "chronicle_entries", ["book_id"], unique=False)
    op.create_index("ix_chronicle_entries_block_id", "chronicle_entries", ["block_id"], unique=False)
    op.create_index("ix_chronicle_entries_actor_id", "chronicle_entries", ["actor_id"], unique=False)
    op.create_index("ix_chronicle_entries_occurred_at", "chronicle_entries", ["occurred_at"], unique=False)
    op.create_index("ix_chronicle_entries_created_at", "chronicle_entries", ["created_at"], unique=False)

    op.create_index(
        "ix_chronicle_entries_book_time",
        "chronicle_entries",
        ["book_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_chronicle_entries_type_time",
        "chronicle_entries",
        ["event_type", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chronicle_entries_type_time", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_book_time", table_name="chronicle_entries")

    op.drop_index("ix_chronicle_entries_created_at", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_occurred_at", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_actor_id", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_block_id", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_book_id", table_name="chronicle_entries")
    op.drop_index("ix_chronicle_entries_event_type", table_name="chronicle_entries")

    op.drop_table("chronicle_entries")

    op.drop_index("idx_chronicle_outbox_error_reason", table_name="chronicle_outbox_events")
    op.drop_index("idx_chronicle_outbox_processing_started", table_name="chronicle_outbox_events")
    op.drop_index("idx_chronicle_outbox_claim", table_name="chronicle_outbox_events")
    op.drop_index("idx_chronicle_outbox_processed", table_name="chronicle_outbox_events")
    op.drop_index("idx_chronicle_outbox_entity", table_name="chronicle_outbox_events")

    op.drop_index("ix_chronicle_outbox_events_error_reason", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_processing_started_at", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_processed_at", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_entity_id", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_entity_type", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_event_version", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_next_retry_at", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_lease_until", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_owner", table_name="chronicle_outbox_events")
    op.drop_index("ix_chronicle_outbox_events_status", table_name="chronicle_outbox_events")

    op.drop_table("chronicle_outbox_events")
