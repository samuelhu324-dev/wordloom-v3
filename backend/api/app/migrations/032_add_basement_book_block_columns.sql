-- Migration 032: Plan173B Basement columns for books & blocks
-- Adds previous_bookshelf_id, moved_to_basement_at on books and deleted_at on blocks
-- Idempotent: uses IF NOT EXISTS + conditional renames so it can run multiple times safely.

BEGIN;

-- 1) Books.previous_bookshelf_id (rename legacy deleted_from_shelf_id when present)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'deleted_from_shelf_id'
    ) THEN
        IF NOT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = 'books' AND column_name = 'previous_bookshelf_id'
        ) THEN
            EXECUTE 'ALTER TABLE books RENAME COLUMN deleted_from_shelf_id TO previous_bookshelf_id';
        ELSE
            EXECUTE 'UPDATE books SET previous_bookshelf_id = COALESCE(previous_bookshelf_id, deleted_from_shelf_id)';
            EXECUTE 'ALTER TABLE books DROP COLUMN deleted_from_shelf_id';
        END IF;
    END IF;
END $$;

ALTER TABLE books
    ADD COLUMN IF NOT EXISTS previous_bookshelf_id UUID REFERENCES bookshelves(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS moved_to_basement_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS idx_books_previous_bookshelf_id ON books(previous_bookshelf_id);
CREATE INDEX IF NOT EXISTS idx_books_moved_to_basement_at ON books(moved_to_basement_at);

COMMENT ON COLUMN books.previous_bookshelf_id IS 'Stores the last active bookshelf before moving into Basement';
COMMENT ON COLUMN books.moved_to_basement_at IS 'Timestamp of the latest move into Basement';

-- 2) Blocks.deleted_at (physical soft delete timestamp used by Plan173B)
ALTER TABLE blocks ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
CREATE INDEX IF NOT EXISTS idx_blocks_deleted_at ON blocks(deleted_at);
COMMENT ON COLUMN blocks.deleted_at IS 'Timestamp of soft delete (Basement/Paperballs alignment)';

COMMIT;
