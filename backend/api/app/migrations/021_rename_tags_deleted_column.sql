-- 021_rename_tags_deleted_column.sql
-- Align tags table with ORM (TagModel.deleted_at)
-- Adds deleted_at column if missing by renaming legacy soft_deleted_at

DO $$
BEGIN
    -- Only rename when legacy column exists and new column absent
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tags' AND column_name = 'soft_deleted_at'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tags' AND column_name = 'deleted_at'
    ) THEN
        EXECUTE 'ALTER TABLE tags RENAME COLUMN soft_deleted_at TO deleted_at';

        -- Rename index if present
        IF EXISTS (
            SELECT 1 FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relname = 'idx_tags_soft_deleted_at'
              AND n.nspname = current_schema()
        ) THEN
            EXECUTE 'ALTER INDEX idx_tags_soft_deleted_at RENAME TO idx_tags_deleted_at';
        END IF;
    ELSIF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tags' AND column_name = 'deleted_at'
    ) THEN
        -- Some databases may lack both columns (fresh install) → add expected column
        EXECUTE 'ALTER TABLE tags ADD COLUMN deleted_at TIMESTAMP NULL';
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_tags_deleted_at ON tags(deleted_at)';
    END IF;
END $$;
