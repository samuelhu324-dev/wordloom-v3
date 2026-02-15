"""Add event_version to search_index

Revision ID: 3c7b2f1a6d11
Revises: 1e9f4c27b2dd
Create Date: 2026-01-27

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c7b2f1a6d11"
down_revision: Union[str, Sequence[str], None] = "1e9f4c27b2dd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "search_index",
        sa.Column(
            "event_version",
            sa.BigInteger(),
            nullable=False,
            server_default="0",
        ),
    )

    # Backfill with a monotonic value derived from updated_at (microsecond resolution).
    # This keeps existing rows compatible with the new anti-regression guard.
    op.execute(
        """
        UPDATE search_index
        SET event_version = GREATEST(
            0,
            FLOOR(EXTRACT(EPOCH FROM updated_at) * 1000000)::bigint
        )
        WHERE event_version = 0;
        """
    )

    op.alter_column("search_index", "event_version", server_default=None)
    op.create_index(
        op.f("ix_search_index_event_version"),
        "search_index",
        ["event_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_search_index_event_version"), table_name="search_index")
    op.drop_column("search_index", "event_version")
