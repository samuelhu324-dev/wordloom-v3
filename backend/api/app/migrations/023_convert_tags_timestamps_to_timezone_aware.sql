-- 023_convert_tags_timestamps_to_timezone_aware.sql
-- Convert timestamp columns in tags and tag_associations from
-- TIMESTAMP WITHOUT TIME ZONE to TIMESTAMP WITH TIME ZONE
-- Date: 2025-11-23
-- Reason: Support timezone-aware datetime.now(timezone.utc) across domain/repository layers

-- Convert tags table timestamps
ALTER TABLE tags
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC',
  ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE USING updated_at AT TIME ZONE 'UTC',
  ALTER COLUMN deleted_at TYPE TIMESTAMP WITH TIME ZONE USING deleted_at AT TIME ZONE 'UTC';

-- Convert tag_associations table timestamps
ALTER TABLE tag_associations
  ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE USING created_at AT TIME ZONE 'UTC';

-- Update default timestamp functions to use timezone-aware versions
ALTER TABLE tags
  ALTER COLUMN created_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC'),
  ALTER COLUMN updated_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC');

ALTER TABLE tag_associations
  ALTER COLUMN created_at SET DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'UTC');
