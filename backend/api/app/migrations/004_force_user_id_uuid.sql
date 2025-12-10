-- Migration 004: Force user_id columns to UUID (drop/recreate)
-- Reason: Previous ALTER TYPE failed (constraints + transaction abort). Empty tables → safe destructive change.
-- Date: 2025-11-19

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Libraries
ALTER TABLE libraries DROP CONSTRAINT IF EXISTS libraries_user_id_key;
DROP INDEX IF EXISTS idx_libraries_user_id;
ALTER TABLE libraries DROP COLUMN user_id;
ALTER TABLE libraries ADD COLUMN user_id uuid NOT NULL;
CREATE INDEX idx_libraries_user_id ON libraries(user_id);
COMMENT ON TABLE libraries IS 'RULE-001 UPDATED: Multi-library per UUID user.';

-- Tags
DROP INDEX IF EXISTS idx_tags_user_id;
ALTER TABLE tags DROP COLUMN user_id;
ALTER TABLE tags ADD COLUMN user_id uuid NOT NULL;
CREATE INDEX idx_tags_user_id ON tags(user_id);

-- Media
DROP INDEX IF EXISTS idx_media_user_id;
ALTER TABLE media DROP COLUMN user_id;
ALTER TABLE media ADD COLUMN user_id uuid NOT NULL;
CREATE INDEX idx_media_user_id ON media(user_id);

-- Chronicle Events
DROP INDEX IF EXISTS idx_chronicle_user_id;
ALTER TABLE chronicle_events DROP COLUMN user_id;
ALTER TABLE chronicle_events ADD COLUMN user_id uuid NOT NULL;
CREATE INDEX idx_chronicle_user_id ON chronicle_events(user_id);

-- Search Index
DROP INDEX IF EXISTS idx_search_index_user_id;
ALTER TABLE search_index DROP COLUMN user_id;
ALTER TABLE search_index ADD COLUMN user_id uuid NOT NULL;
CREATE INDEX idx_search_index_user_id ON search_index(user_id);
