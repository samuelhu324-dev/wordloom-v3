"""chronicle_envelope_server_defaults

Revision ID: 6c2c2d3a7e11
Revises: 35f0c87d13c5
Create Date: 2026-02-04

Phase C follow-up:
- Add server_default for promoted envelope columns (without NOT NULL).
- Purpose: ensure new writes don't accidentally produce NULLs if any edge path misses injection.

Defaults are intentionally conservative:
- schema_version: 1
- provenance/source/actor_kind: 'unknown'
- correlation_id: no default (NULL is meaningful; do not fabricate).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "6c2c2d3a7e11"
down_revision: Union[str, Sequence[str], None] = "35f0c87d13c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "chronicle_events",
        "schema_version",
        existing_type=sa.Integer(),
        server_default=sa.text("1"),
    )
    op.alter_column(
        "chronicle_events",
        "provenance",
        existing_type=sa.String(length=32),
        server_default=sa.text("'unknown'"),
    )
    op.alter_column(
        "chronicle_events",
        "source",
        existing_type=sa.String(length=64),
        server_default=sa.text("'unknown'"),
    )
    op.alter_column(
        "chronicle_events",
        "actor_kind",
        existing_type=sa.String(length=32),
        server_default=sa.text("'unknown'"),
    )


def downgrade() -> None:
    op.alter_column(
        "chronicle_events",
        "actor_kind",
        existing_type=sa.String(length=32),
        server_default=None,
    )
    op.alter_column(
        "chronicle_events",
        "source",
        existing_type=sa.String(length=64),
        server_default=None,
    )
    op.alter_column(
        "chronicle_events",
        "provenance",
        existing_type=sa.String(length=32),
        server_default=None,
    )
    op.alter_column(
        "chronicle_events",
        "schema_version",
        existing_type=sa.Integer(),
        server_default=None,
    )
