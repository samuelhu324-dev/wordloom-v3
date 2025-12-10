-- Migration 016: Add todo_list block type to valid_block_type constraint
-- Goal: allow backend to persist the new todo_list BlockType introduced for checkbox todos.
-- Strategy: refresh the CHECK constraint so it includes the new value while staying idempotent.

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.table_constraints
    WHERE table_name='blocks' AND constraint_name='valid_block_type'
  ) THEN
    ALTER TABLE blocks DROP CONSTRAINT valid_block_type;
  END IF;
END$$;

ALTER TABLE blocks
  ADD CONSTRAINT valid_block_type
  CHECK (type IN ('text','heading','code','image','quote','list','todo_list','table','divider'));

COMMIT;

-- Verification:
--   SELECT DISTINCT type FROM blocks ORDER BY 1;
--
