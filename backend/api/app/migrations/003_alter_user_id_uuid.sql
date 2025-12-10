-- Migration 003: Align user_id columns to UUID across core tables
-- Reason: Domain models use UUID user_id; initial schema used INT causing insert failures
-- Date: 2025-11-19
-- Safe: No existing data (tables empty) so we can alter types freely

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Libraries
ALTER TABLE libraries
    ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_libraries_user_id;
CREATE INDEX idx_libraries_user_id ON libraries(user_id);
COMMENT ON TABLE libraries IS 'RULE-001 (UPDATED): Multi-library per UUID user.';

-- Tags
ALTER TABLE tags
    ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_tags_user_id;
CREATE INDEX idx_tags_user_id ON tags(user_id);

-- Media
ALTER TABLE media
    ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_media_user_id;
CREATE INDEX idx_media_user_id ON media(user_id);

-- Chronicle Events
ALTER TABLE chronicle_events
    ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_chronicle_user_id;
CREATE INDEX idx_chronicle_user_id ON chronicle_events(user_id);

-- Search Index
ALTER TABLE search_index
    ALTER COLUMN user_id TYPE uuid USING gen_random_uuid();
DROP INDEX IF EXISTS idx_search_index_user_id;
CREATE INDEX idx_search_index_user_id ON search_index(user_id);
