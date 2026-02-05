"""phase_c_chronicle_envelope_columns

Revision ID: 35f0c87d13c5
Revises: 2d7f6a1c9b0e
Create Date: 2026-02-04 18:42:38.009837

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35f0c87d13c5'
down_revision: Union[str, Sequence[str], None] = '2d7f6a1c9b0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("chronicle_events", sa.Column("schema_version", sa.Integer(), nullable=True))
    op.add_column("chronicle_events", sa.Column("provenance", sa.String(length=32), nullable=True))
    op.add_column("chronicle_events", sa.Column("source", sa.String(length=64), nullable=True))
    op.add_column("chronicle_events", sa.Column("actor_kind", sa.String(length=32), nullable=True))
    op.add_column("chronicle_events", sa.Column("correlation_id", sa.String(length=128), nullable=True))

    # Backfill from payload envelope (safe for JSON/JSONB).
    op.execute(
        """
        UPDATE chronicle_events
        SET
            schema_version = COALESCE(schema_version, NULLIF(payload->>'schema_version', '')::int, 1),
            provenance     = COALESCE(provenance, NULLIF(payload->>'provenance', ''), 'unknown'),
            source         = COALESCE(source, NULLIF(payload->>'source', ''), 'unknown'),
            actor_kind     = COALESCE(actor_kind, NULLIF(payload->>'actor_kind', ''), 'unknown'),
            correlation_id = COALESCE(correlation_id, NULLIF(payload->>'correlation_id', ''))
        WHERE
            schema_version IS NULL
            OR provenance IS NULL
            OR source IS NULL
            OR actor_kind IS NULL
            OR correlation_id IS NULL
        """
    )

    op.create_index(
        "ix_chronicle_events_correlation_id",
        "chronicle_events",
        ["correlation_id"],
        unique=False,
    )
    op.create_index(
        "ix_chronicle_events_source_time",
        "chronicle_events",
        ["source", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_chronicle_events_source_time", table_name="chronicle_events")
    op.drop_index("ix_chronicle_events_correlation_id", table_name="chronicle_events")

    op.drop_column("chronicle_events", "correlation_id")
    op.drop_column("chronicle_events", "actor_kind")
    op.drop_column("chronicle_events", "source")
    op.drop_column("chronicle_events", "provenance")
    op.drop_column("chronicle_events", "schema_version")
