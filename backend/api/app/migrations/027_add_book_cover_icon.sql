-- Migration 027: Add cover_icon column to books table
-- Context: Plan88 (Nov 28, 2025) introduces optional Lucide cover icons for books

ALTER TABLE books
    ADD COLUMN IF NOT EXISTS cover_icon VARCHAR(64);

ALTER TABLE books
    ADD CONSTRAINT check_books_cover_icon_slug
    CHECK (cover_icon IS NULL OR cover_icon ~ '^[a-z0-9\-]+$');

COMMENT ON COLUMN books.cover_icon IS 'POLICY-BOOK-COVER-ICON-LUCIDE: Optional Lucide icon name (<=64 ASCII chars).';
