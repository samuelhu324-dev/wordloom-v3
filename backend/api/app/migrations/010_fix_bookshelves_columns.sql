-- Migration 010: Align bookshelves table with ORM/domain expectations
-- Adds missing columns (is_pinned, pinned_at, is_favorite, book_count)
-- Normalizes status values to lowercase and updates defaults/triggers
-- Safe to run multiple times (IF NOT EXISTS / idempotent updates)

BEGIN;

-- 1. Add missing columns used by ORM model
ALTER TABLE bookshelves ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE bookshelves ADD COLUMN IF NOT EXISTS pinned_at TIMESTAMPTZ NULL;
ALTER TABLE bookshelves ADD COLUMN IF NOT EXISTS is_favorite BOOLEAN DEFAULT FALSE NOT NULL;
ALTER TABLE bookshelves ADD COLUMN IF NOT EXISTS book_count INT DEFAULT 0 NOT NULL;

-- 2. Normalize existing status values (uppercase -> lowercase)
UPDATE bookshelves SET status = LOWER(status) WHERE status != LOWER(status);

-- 3. Adjust default to lowercase 'active'
ALTER TABLE bookshelves ALTER COLUMN status SET DEFAULT 'active';

-- 4. Update trigger function to insert lowercase status for Basement bookshelf
CREATE OR REPLACE FUNCTION create_library_basement()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO bookshelves (library_id, name, is_basement, status)
    VALUES (NEW.id, 'Basement', TRUE, 'active');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Verification hints (run manually):
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name='bookshelves';
-- SELECT DISTINCT status FROM bookshelves;
