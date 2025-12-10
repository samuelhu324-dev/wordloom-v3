-- Migration 014: Force rename legacy blocks.block_type -> type (hotfix)
-- Date: 2025-11-21
-- Problem: Production/dev table still has column block_type; ORM now expects type.
--          Previous conditional migrations may not have executed. This hotfix performs:
--            1. If block_type exists AND type missing -> rename.
--            2. If both exist (rare) -> copy data from block_type into type then drop block_type.
--            3. Ensure valid_block_type CHECK constraint present.
--            4. Ensure type column NOT NULL default 'text'.
-- Idempotent: Safe to re-run; does nothing if final state already achieved.

BEGIN;

DO $$
DECLARE
  has_type BOOLEAN;
  has_block_type BOOLEAN;
BEGIN
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='type') INTO has_type;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='block_type') INTO has_block_type;

  -- Case 1: legacy only
  IF has_block_type AND NOT has_type THEN
    ALTER TABLE blocks RENAME COLUMN block_type TO type;
    has_type := TRUE;
    has_block_type := FALSE; -- after rename
  END IF;

  -- Case 2: both columns somehow present (partial previous attempt)
  IF has_block_type AND has_type THEN
    EXECUTE 'UPDATE blocks SET type = COALESCE(block_type, type)';
    ALTER TABLE blocks DROP COLUMN block_type;
  END IF;
END$$;

-- Ensure type column default + not null
ALTER TABLE blocks ALTER COLUMN type SET DEFAULT 'text';
UPDATE blocks SET type='text' WHERE type IS NULL;
ALTER TABLE blocks ALTER COLUMN type SET NOT NULL;

-- Refresh valid_block_type constraint
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
--   SELECT column_name FROM information_schema.columns WHERE table_name='blocks' AND column_name IN ('type','block_type');
--   \d+ blocks
--   SELECT type, COUNT(*) FROM blocks GROUP BY type;