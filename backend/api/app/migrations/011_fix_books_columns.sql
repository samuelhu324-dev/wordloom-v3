-- Migration 011: Align books table with new BookModel/domain (Nov 20 2025)
-- Adds missing columns (is_pinned, block_count, due_at) required by current ORM
-- Normalizes status values to lowercase and sets default to 'draft'
-- Idempotent: uses IF NOT EXISTS and safe UPDATE patterns

BEGIN;

-- 1. Add new columns required by BookModel
ALTER TABLE books ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE books ADD COLUMN IF NOT EXISTS block_count INT NOT NULL DEFAULT 0;
ALTER TABLE books ADD COLUMN IF NOT EXISTS due_at TIMESTAMPTZ NULL;

-- 2. Normalize existing status values to lowercase (domain now uses lowercase lifecycle)
UPDATE books SET status = LOWER(status) WHERE status <> LOWER(status);

-- 3. Ensure default status is 'draft' for new records (matches BookModel)
ALTER TABLE books ALTER COLUMN status SET DEFAULT 'draft';

-- 4. (Optional future cleanup) Legacy columns retained for backward compatibility:
--    author, isbn, priority, urgency, due_date, pages_total, reading_progress, last_read_at,
--    deleted_from_shelf_id. They can be removed in a later deprecation migration when confirmed unused.

COMMIT;

-- Verification hints:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name='books';
-- SELECT DISTINCT status FROM books;
-- SELECT is_pinned, block_count, due_at FROM books LIMIT 5;
