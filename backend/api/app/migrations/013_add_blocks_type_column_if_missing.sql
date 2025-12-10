-- Migration 013: Add blocks.type column if missing (safety after Phase0 refactor)
-- Date: 2025-11-21
-- Purpose: Some environments still have legacy `block_type` or lack `type` due to skipped Migration 012.
--          This migration ensures `type` column exists with expected enum values.
--          If `block_type` exists and `type` is absent, it renames. If neither exists, it creates.
--          Idempotent: safe to re-run.

BEGIN;

-- 1. Rename legacy block_type -> type if needed
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='block_type'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='type'
  ) THEN
    ALTER TABLE blocks RENAME COLUMN block_type TO type;
  END IF;
END$$;

-- 2. Create type column if still missing (default 'text')
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='type'
  ) THEN
    ALTER TABLE blocks ADD COLUMN type VARCHAR(32) NOT NULL DEFAULT 'text';
  END IF;
END$$;

-- 3. Normalize existing NULLs (defensive)
UPDATE blocks SET type='text' WHERE type IS NULL;

-- 4. Add / replace constraint for valid values (if enum not yet enforced)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_name='blocks' AND constraint_name='valid_block_type'
  ) THEN
    ALTER TABLE blocks DROP CONSTRAINT valid_block_type;
  END IF;
  ALTER TABLE blocks ADD CONSTRAINT valid_block_type CHECK (type IN (
    'text','heading','code','image','quote','list','table','divider'
  ));
END$$;

COMMIT;

-- Verification:
--   SELECT type, COUNT(*) FROM blocks GROUP BY type;
--   \d+ blocks