-- Migration 017: Add media_type column to media table
-- Reason: ORM model requires media_type (IMAGE | VIDEO) but database was missing it
-- Date: 2025-11-22

-- Add media_type column to media table
-- Default to 'image' for existing records (assumes most existing media are images)
ALTER TABLE media ADD COLUMN media_type VARCHAR(20) DEFAULT 'image' NOT NULL;

-- Add check constraint for valid media types
ALTER TABLE media ADD CONSTRAINT valid_media_type CHECK (media_type IN ('image', 'video'));

-- Create index for media_type for potential future queries
CREATE INDEX idx_media_type ON media(media_type);

-- Update comment on column
COMMENT ON COLUMN media.media_type IS 'Type of media: image or video';
