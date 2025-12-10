-- Migration 016: Allow Anonymous Media Owners
-- Purpose: Permit media uploads without an associated user by allowing NULL user_id values.
-- Strategy: Drop the NOT NULL constraint on media.user_id only if it is currently enforced.

BEGIN;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'media'
      AND column_name = 'user_id'
      AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE media ALTER COLUMN user_id DROP NOT NULL;
  END IF;
END$$;

COMMIT;

-- Verification:
--   SELECT column_name, is_nullable FROM information_schema.columns
--   WHERE table_name='media' AND column_name='user_id';
