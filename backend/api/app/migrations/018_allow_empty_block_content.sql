-- Migration 018: Allow empty block content for placeholder blocks
-- Date: 2025-11-27
-- Reason: Frontend now inserts empty paragraph blocks by default

-- Drop the old constraint that rejected zero-length content (trimmed)
ALTER TABLE blocks DROP CONSTRAINT IF EXISTS check_content_not_empty;

-- Allow empty strings but keep content non-null for compatibility
ALTER TABLE blocks ADD CONSTRAINT check_content_not_empty CHECK (content IS NOT NULL);
