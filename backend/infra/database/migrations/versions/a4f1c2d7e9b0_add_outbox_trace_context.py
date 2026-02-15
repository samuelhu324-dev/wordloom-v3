"""Add trace context fields to outbox tables.

Revision ID: a4f1c2d7e9b0
Revises: 9c41e07a2c1b
Create Date: 2026-02-08

Purpose:
- Allow API → outbox enqueue to persist W3C trace context.
- Allow worker processes to continue the same trace when processing events.

Fields:
- traceparent (W3C Trace Context)
- tracestate (optional)

Both are nullable and best-effort.
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4f1c2d7e9b0"
down_revision: Union[str, Sequence[str], None] = "9c41e07a2c1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("search_outbox_events", sa.Column("traceparent", sa.String(length=512), nullable=True))
    op.add_column("search_outbox_events", sa.Column("tracestate", sa.Text(), nullable=True))

    op.add_column("chronicle_outbox_events", sa.Column("traceparent", sa.String(length=512), nullable=True))
    op.add_column("chronicle_outbox_events", sa.Column("tracestate", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("chronicle_outbox_events", "tracestate")
    op.drop_column("chronicle_outbox_events", "traceparent")

    op.drop_column("search_outbox_events", "tracestate")
    op.drop_column("search_outbox_events", "traceparent")
