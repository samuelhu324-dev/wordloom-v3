"""chronicle_block_updated_dedupe_state

Revision ID: 9c41e07a2c1b
Revises: 6c2c2d3a7e11
Create Date: 2026-02-05

Create a small dedupe/rate-limit state table used to suppress high-frequency
Chronicle facts (multi-instance consistent via Postgres upsert).

We deliberately keep this table bounded (one row per key) instead of storing
one row per time bucket.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "9c41e07a2c1b"
down_revision: Union[str, Sequence[str], None] = "6c2c2d3a7e11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chronicle_event_dedupe_state",
        sa.Column("event_type", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("book_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("block_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("window_seconds", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("last_bucket", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.id"], ondelete="CASCADE"),
    )

    op.create_index(
        "ix_chronicle_event_dedupe_state_updated",
        "chronicle_event_dedupe_state",
        ["updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_chronicle_event_dedupe_state_updated", table_name="chronicle_event_dedupe_state")
    op.drop_table("chronicle_event_dedupe_state")
