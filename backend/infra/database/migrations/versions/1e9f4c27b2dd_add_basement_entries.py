"""Add basement entries projection table

Revision ID: 1e9f4c27b2dd
Revises: 59e8b1031657
Create Date: 2025-12-12 12:34:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1e9f4c27b2dd"
down_revision: Union[str, Sequence[str], None] = "59e8b1031657"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create basement_entries table (idempotent).

    This revision originally created the table via Alembic ops.
    We keep it *idempotent* so it can run safely even after
    init schema was updated to include basement_entries.
    """

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS basement_entries (
            id UUID PRIMARY KEY,
            book_id UUID NOT NULL UNIQUE,
            library_id UUID NOT NULL,
            bookshelf_id UUID,
            previous_bookshelf_id UUID,
            title_snapshot VARCHAR(255) NOT NULL,
            summary_snapshot TEXT,
            status_snapshot VARCHAR(50) NOT NULL,
            block_count_snapshot INTEGER NOT NULL DEFAULT 0,
            moved_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            CONSTRAINT fk_basement_book FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            CONSTRAINT fk_basement_library FOREIGN KEY (library_id) REFERENCES libraries(id) ON DELETE CASCADE,
            CONSTRAINT fk_basement_bookshelf FOREIGN KEY (bookshelf_id) REFERENCES bookshelves(id) ON DELETE SET NULL
        );

        CREATE INDEX IF NOT EXISTS idx_basement_entries_book_id ON basement_entries(book_id);
        CREATE INDEX IF NOT EXISTS idx_basement_entries_library_id ON basement_entries(library_id);
        CREATE INDEX IF NOT EXISTS idx_basement_entries_moved_at ON basement_entries(moved_at DESC);

        COMMENT ON TABLE basement_entries IS 'Snapshot records of books currently in Basement recycle area';
        COMMENT ON COLUMN basement_entries.book_id IS 'FK to books table (CASCADE on delete)';
        COMMENT ON COLUMN basement_entries.previous_bookshelf_id IS 'Last active bookshelf before entering Basement';
        COMMENT ON COLUMN basement_entries.moved_at IS 'Timestamp when book entered Basement';
        """
    )


def downgrade() -> None:
    """Drop basement_entries table and indexes (idempotent)."""
    op.execute(
        """
        DROP INDEX IF EXISTS idx_basement_entries_moved_at;
        DROP INDEX IF EXISTS idx_basement_entries_library_id;
        DROP INDEX IF EXISTS idx_basement_entries_book_id;
        DROP TABLE IF EXISTS basement_entries CASCADE;
        """
    )
