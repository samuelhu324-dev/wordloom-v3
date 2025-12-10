-- Migration 033: Add basement_entries table
-- Purpose: Dedicated projection for books in the Basement recycle area (Plan173E)
-- Date: 2025-12-06

-- Rollback commands (if needed):
-- DROP INDEX IF EXISTS idx_basement_entries_book_id;
-- DROP INDEX IF EXISTS idx_basement_entries_library_id;
-- DROP INDEX IF EXISTS idx_basement_entries_moved_at;
-- DROP TABLE IF EXISTS basement_entries CASCADE;

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
