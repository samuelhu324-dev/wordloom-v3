-- Migration 018: Library Activity, Pinning, and View Metrics
-- Purpose: Support Plan 20 library sorting (last activity, pinned segment, archive state) and persist view statistics.
-- Changes:
--   * Add last_activity_at, pinned, pinned_order, archived_at, views_count, last_viewed_at columns.
--   * Backfill activity timestamps for existing data.
--   * Introduce helper functions and triggers to keep last_activity_at in sync with bookshelf/book/block operations.
--   * Create supporting indexes for sorting and filtering.

BEGIN;

-- === Schema changes ===
ALTER TABLE libraries
  ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS pinned BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS pinned_order INTEGER,
  ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS views_count BIGINT NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS last_viewed_at TIMESTAMP WITH TIME ZONE;

-- Backfill last_activity_at using the freshest known timestamp.
UPDATE libraries
SET last_activity_at = COALESCE(last_activity_at, updated_at, created_at, NOW())
WHERE last_activity_at IS NULL;

-- Ensure future inserts default to current UTC timestamp.
ALTER TABLE libraries
  ALTER COLUMN last_activity_at SET DEFAULT (timezone('utc', now()));

-- Enforce NOT NULL after backfill.
ALTER TABLE libraries
  ALTER COLUMN last_activity_at SET NOT NULL;

-- === Indexes to support sorting/filters ===
CREATE INDEX IF NOT EXISTS idx_libraries_last_activity_at ON libraries (last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_libraries_pinned_order ON libraries (pinned DESC, pinned_order ASC);
CREATE INDEX IF NOT EXISTS idx_libraries_archived_at ON libraries (archived_at);
CREATE INDEX IF NOT EXISTS idx_libraries_views_count ON libraries (views_count DESC);

-- === Helper function: touch library activity ===
CREATE OR REPLACE FUNCTION touch_library_activity(library_uuid UUID)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  IF library_uuid IS NULL THEN
    RETURN;
  END IF;
  UPDATE libraries
  SET last_activity_at = timezone('utc', now()),
      updated_at = timezone('utc', now())
  WHERE id = library_uuid;
END;
$$;

-- === Trigger for bookshelves (direct library_id) ===
CREATE OR REPLACE FUNCTION touch_library_from_bookshelves()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  lib_id UUID;
BEGIN
  IF TG_OP = 'DELETE' THEN
    lib_id := OLD.library_id;
  ELSE
    lib_id := NEW.library_id;
  END IF;
  PERFORM touch_library_activity(lib_id);
  RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_bookshelves_touch_library ON bookshelves;
CREATE TRIGGER trg_bookshelves_touch_library
AFTER INSERT OR UPDATE OR DELETE
ON bookshelves
FOR EACH ROW
EXECUTE FUNCTION touch_library_from_bookshelves();

-- === Trigger for books (library_id redundant column) ===
CREATE OR REPLACE FUNCTION touch_library_from_books()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  lib_id UUID;
BEGIN
  IF TG_OP = 'DELETE' THEN
    lib_id := OLD.library_id;
  ELSE
    lib_id := NEW.library_id;
  END IF;
  PERFORM touch_library_activity(lib_id);
  RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_books_touch_library ON books;
CREATE TRIGGER trg_books_touch_library
AFTER INSERT OR UPDATE OR DELETE
ON books
FOR EACH ROW
EXECUTE FUNCTION touch_library_from_books();

-- === Trigger for blocks (lookup via books table) ===
CREATE OR REPLACE FUNCTION touch_library_from_blocks()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  lib_id UUID;
BEGIN
  IF TG_OP = 'DELETE' THEN
    SELECT b.library_id INTO lib_id FROM books b WHERE b.id = OLD.book_id;
  ELSE
    SELECT b.library_id INTO lib_id FROM books b WHERE b.id = NEW.book_id;
  END IF;
  IF lib_id IS NOT NULL THEN
    PERFORM touch_library_activity(lib_id);
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$;

DROP TRIGGER IF EXISTS trg_blocks_touch_library ON blocks;
CREATE TRIGGER trg_blocks_touch_library
AFTER INSERT OR UPDATE OR DELETE
ON blocks
FOR EACH ROW
EXECUTE FUNCTION touch_library_from_blocks();

COMMIT;

-- Verification snippets:
--   SELECT last_activity_at, pinned, pinned_order, archived_at, views_count FROM libraries;
--
--   -- Test trigger: insert into bookshelves/books/blocks and confirm libraries.last_activity_at updates.
