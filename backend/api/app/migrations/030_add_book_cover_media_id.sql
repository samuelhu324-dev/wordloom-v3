-- Migration 030: Add cover_media_id column for Book custom covers
-- Context: Plan_108 / ADR-115 stable-only cover media pipeline

ALTER TABLE books
    ADD COLUMN IF NOT EXISTS cover_media_id UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_books_cover_media'
            AND table_name = 'books'
    ) THEN
        ALTER TABLE books
            ADD CONSTRAINT fk_books_cover_media
            FOREIGN KEY (cover_media_id)
            REFERENCES media(id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_books_cover_media_id
    ON books(cover_media_id);

COMMENT ON COLUMN books.cover_media_id IS 'POLICY-BOOK-COVER-MEDIA-STABLE-ONLY: Optional Media UUID for uploaded book covers.';
