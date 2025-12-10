-- Migration 015: Phase0 Blocks Alignment Hotfix (idempotent)
-- Purpose: Complete column renames & additions after 012 partial failure
-- Issues fixed:
--   - Table still uses sort_key instead of "order"
--   - deleted_prev_block_id / deleted_next_block_id not renamed
--   - heading_level / meta columns missing
--   - precision of ordering column still NUMERIC(20,10)
-- Strategy:
--   Drop dependent view active_blocks, apply renames & type changes, recreate view.
--   Safe to re-run (IF NOT EXISTS guards / existence checks).

BEGIN;

-- 1. Drop dependent view to allow column rename/type changes
DROP VIEW IF EXISTS active_blocks;

-- 2. Rename columns if legacy names present
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='sort_key')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='order') THEN
    ALTER TABLE blocks RENAME COLUMN sort_key TO "order";
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_prev_block_id')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_prev_id') THEN
    ALTER TABLE blocks RENAME COLUMN deleted_prev_block_id TO deleted_prev_id;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_next_block_id')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_next_id') THEN
    ALTER TABLE blocks RENAME COLUMN deleted_next_block_id TO deleted_next_id;
  END IF;
END$$;

-- 3. Add missing columns
ALTER TABLE blocks ADD COLUMN IF NOT EXISTS heading_level INT NULL;
ALTER TABLE blocks ADD COLUMN IF NOT EXISTS meta TEXT NULL;

-- 4. Adjust fractional ordering precision if below target
DO $$
DECLARE
  prec INTEGER;
  scale INTEGER;
BEGIN
  SELECT numeric_precision, numeric_scale INTO prec, scale
  FROM information_schema.columns WHERE table_name='blocks' AND column_name='order';
  IF prec IS NOT NULL AND (prec < 36 OR scale < 18) THEN
    ALTER TABLE blocks ALTER COLUMN "order" TYPE NUMERIC(36,18) USING "order"::numeric;
  END IF;
END$$;

-- 5. Refresh valid_block_type constraint to current supported set
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.table_constraints WHERE table_name='blocks' AND constraint_name='valid_block_type') THEN
    ALTER TABLE blocks DROP CONSTRAINT valid_block_type;
  END IF;
  ALTER TABLE blocks ADD CONSTRAINT valid_block_type CHECK (type IN ('text','heading','code','image','quote','list','table','divider'));
END$$;

-- 6. Recreate view
CREATE VIEW active_blocks AS SELECT * FROM blocks WHERE soft_deleted_at IS NULL;

COMMIT;

-- Verification:
--   SELECT column_name FROM information_schema.columns WHERE table_name='blocks';
--   \d+ blocks (psql)
--   SELECT type, COUNT(*) FROM blocks GROUP BY type;