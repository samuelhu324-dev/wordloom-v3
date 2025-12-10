-- 031_add_library_theme_color.sql
-- Adds a dedicated theme_color column so libraries can store explicit palette choices

ALTER TABLE libraries
    ADD COLUMN IF NOT EXISTS theme_color VARCHAR(16);
