"""Add search_index.library_id scope key

Revision ID: d1f0a9b3c2e4
Revises: c9a4fd28c0b4
Create Date: 2026-02-02

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "d1f0a9b3c2e4"
down_revision: Union[str, Sequence[str], None] = "c9a4fd28c0b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "search_index",
        sa.Column("library_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Backfill known library-scoped entity types.
    # 1) blocks: search_index.entity_id == blocks.id → books.library_id
    op.execute(
        """
        UPDATE search_index si
        SET library_id = b.library_id
        FROM blocks bl
        JOIN books b ON b.id = bl.book_id
        WHERE si.entity_type = 'block'
          AND si.entity_id = bl.id
        """
    )

    # 2) books: search_index.entity_id == books.id → books.library_id
    op.execute(
        """
        UPDATE search_index si
        SET library_id = b.library_id
        FROM books b
        WHERE si.entity_type = 'book'
          AND si.entity_id = b.id
        """
    )

    op.create_index(
        "idx_search_index_library_type",
        "search_index",
        ["library_id", "entity_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_search_index_library_type", table_name="search_index")
    op.drop_column("search_index", "library_id")
