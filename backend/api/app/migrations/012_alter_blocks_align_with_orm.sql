-- Migration 012: Align blocks table with revised ORM/Domain (Phase 0)
-- Date: 2025-11-21
-- Purpose:
--   1. Rename legacy columns to match ORM (block_type -> type, sort_key -> order,
--      deleted_prev_block_id -> deleted_prev_id, deleted_next_block_id -> deleted_next_id)
--   2. Increase fractional index precision from NUMERIC(20,10) to NUMERIC(36,18)
--      to reduce collision risk per ADR-080 ordering strategy.
--   3. Add heading_level (INT NULL) for HEADING blocks (H1=1,H2=2,H3=3).
--   4. Add meta (TEXT NULL) reserved for future lightweight metadata (Phase 0 does not use yet).
--   5. Update valid_block_type constraint to current supported set
--      ('text','heading','code','image','quote','list','table','divider').
--   6. Add content length hard limit (20KB) check constraint (BLOCK_CONTENT_TOO_LARGE domain rule).
--   7. Idempotent & safe: checks existence before altering where feasible.
--
-- Notes:
--   - Existing data preserved. New precision conversion uses explicit USING cast.
--   - Language & collapsed legacy columns retained (backward compatibility) though unused by ORM.
--   - Paperballs recovery columns renamed only; data retained.
--   - If previous migration partially applied (e.g., some columns already renamed), blocks of code skip.
--
-- Rollback (manual outline):
--   - Rename columns back, revert precision to NUMERIC(20,10), drop heading_level/meta, restore old constraint.
--
-- Verification after migration:
--   SELECT column_name, data_type FROM information_schema.columns WHERE table_name='blocks';
--
--
BEGIN;

-- 1. Rename columns (guard with existence checks via DO blocks)
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

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='sort_key'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='order'
  ) THEN
    ALTER TABLE blocks RENAME COLUMN sort_key TO "order"; -- order is keyword; quoted once here
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_prev_block_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_prev_id'
  ) THEN
    ALTER TABLE blocks RENAME COLUMN deleted_prev_block_id TO deleted_prev_id;
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_next_block_id'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_name='blocks' AND column_name='deleted_next_id'
  ) THEN
    ALTER TABLE blocks RENAME COLUMN deleted_next_block_id TO deleted_next_id;
  END IF;
END$$;

-- 2. Alter fractional index precision (to NUMERIC(36,18)) if current precision < desired
DO $$
DECLARE
  prec INTEGER;
  scale INTEGER;
BEGIN
  SELECT numeric_precision, numeric_scale
  INTO prec, scale
  FROM information_schema.columns
  WHERE table_name='blocks' AND column_name='order';

  IF prec IS NOT NULL THEN
    IF (prec < 36 OR scale < 18) THEN
      ALTER TABLE blocks ALTER COLUMN "order" TYPE NUMERIC(36,18) USING "order"::numeric;
    END IF;
  END IF;
END$$;

-- 3. Add heading_level column if missing
ALTER TABLE blocks ADD COLUMN IF NOT EXISTS heading_level INT NULL;

-- 4. Add meta column if missing
ALTER TABLE blocks ADD COLUMN IF NOT EXISTS meta TEXT NULL;

-- 5. Update valid_block_type constraint (drop + recreate)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints tc
    WHERE tc.table_name='blocks' AND tc.constraint_type='CHECK' AND tc.constraint_name='valid_block_type'
  ) THEN
    ALTER TABLE blocks DROP CONSTRAINT valid_block_type;
  END IF;

  ALTER TABLE blocks ADD CONSTRAINT valid_block_type CHECK (type IN (
    'text','heading','code','image','quote','list','table','divider'
  ));
END$$;

-- 6. Add content length constraint (20KB bytes) if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.table_constraints tc
    WHERE tc.table_name='blocks' AND tc.constraint_type='CHECK' AND tc.constraint_name='chk_blocks_content_length'
  ) THEN
    ALTER TABLE blocks ADD CONSTRAINT chk_blocks_content_length CHECK (octet_length(content) <= 20000);
  END IF;
END$$;

COMMIT;

-- Post-migration verification suggestions:
--   \d+ blocks
--   SELECT id, type, order, heading_level, octet_length(content) FROM blocks LIMIT 5;
--   SELECT pg_size_pretty(pg_relation_size('blocks'));
