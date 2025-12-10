-- 022_add_tags_level_column.sql
-- Ensure tags table has hierarchical level metadata for TagModel parity

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'tags'
          AND column_name = 'level'
    ) THEN
        ALTER TABLE tags
        ADD COLUMN level INT NOT NULL DEFAULT 0;
    END IF;
END
$$;

-- Backfill any existing rows to the default hierarchy level
UPDATE tags SET level = COALESCE(level, 0);

-- Ensure we keep an index for planner friendliness when filtering by level
CREATE INDEX IF NOT EXISTS idx_tags_level ON tags(level);
