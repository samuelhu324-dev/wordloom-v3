-- Migration 017: Add media_type column to media table
-- Date: 2025-11-22
-- Reason: media_type was missing from database but required by ORM model

ALTER TABLE media ADD COLUMN media_type VARCHAR(50) NOT NULL DEFAULT 'image';

-- Create check constraint for valid media types
ALTER TABLE media ADD CONSTRAINT valid_media_type CHECK (media_type IN ('image', 'video'));

-- Create index on media_type for future queries
CREATE INDEX idx_media_type ON media(media_type);

COMMENT ON COLUMN media.media_type IS 'Type of media: image or video';
