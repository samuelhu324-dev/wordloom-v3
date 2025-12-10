-- Migration 026: Allow empty block content for placeholder paragraphs
-- Date: 2025-11-27
-- Purpose: unblock frontend auto-insertion of blank paragraph blocks

-- 1. Drop legacy constraint that trimmed content and enforced length>0
ALTER TABLE blocks DROP CONSTRAINT IF EXISTS check_content_not_empty;

-- 2. Replace with a lighter guard: keep content non-null but allow empty string
ALTER TABLE blocks ADD CONSTRAINT check_content_not_empty CHECK (content IS NOT NULL);
