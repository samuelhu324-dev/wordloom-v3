-- Migration 002: Multi-Library + Description + Cover Support
-- Date: 2025-11-18
-- Purpose:
--   1. Remove UNIQUE constraint on libraries.user_id (allow multiple libraries per user)
--   2. Ensure description column exists (TEXT NULL)
--   3. Add cover_media_id column (UUID NULL) for Media association (one primary cover)
--   4. Add index on cover_media_id for quick retrieval
--   5. Update comments to reflect new RULE-001 (Unlimited libraries per user)
--
-- Idempotent guards: Use IF EXISTS / IF NOT EXISTS to allow re-run without errors

-- 1. Drop UNIQUE constraint (name may differ if created automatically)
-- Attempt common patterns; ignore errors if already dropped
DO $$
BEGIN
    BEGIN
        ALTER TABLE libraries DROP CONSTRAINT IF EXISTS libraries_user_id_key; -- implicit name pattern
    EXCEPTION WHEN undefined_object THEN NULL; END;
    BEGIN
        ALTER TABLE libraries DROP CONSTRAINT IF EXISTS unique_user_id; -- alternative custom name
    EXCEPTION WHEN undefined_object THEN NULL; END;
    BEGIN
        -- If still unique via index
        DROP INDEX IF EXISTS libraries_user_id_key;
    EXCEPTION WHEN undefined_table THEN NULL; END;
END$$;

-- 2. Ensure description column exists (older schema may already have it)
ALTER TABLE libraries ADD COLUMN IF NOT EXISTS description TEXT NULL;

-- 3. Add cover_media_id (UUID FK optional)
ALTER TABLE libraries ADD COLUMN IF NOT EXISTS cover_media_id UUID NULL;
-- Optional FK to media (not enforced to allow decoupled deletion)
-- ALTER TABLE libraries ADD CONSTRAINT fk_libraries_cover_media FOREIGN KEY (cover_media_id) REFERENCES media(id) ON DELETE SET NULL;

-- 4. Add index for cover_media_id
CREATE INDEX IF NOT EXISTS idx_libraries_cover_media_id ON libraries(cover_media_id);

-- 5. Update table comment
COMMENT ON TABLE libraries IS 'RULE-001 (UPDATED): User can have multiple libraries (indexed user_id).';

-- 6. Ensure user_id index remains (add if missing after constraint drop)
CREATE INDEX IF NOT EXISTS idx_libraries_user_id ON libraries(user_id);

-- Verification Query (manual run):
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name='libraries';
-- SELECT * FROM libraries LIMIT 5;
