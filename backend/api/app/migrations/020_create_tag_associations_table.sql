-- Migration 020: Create tag_associations table for cross-entity tag links
-- Resolves missing relation error when loading Library tags (Plan_31 Option A)

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type WHERE typname = 'enum_tag_associations_entity_type'
    ) THEN
        CREATE TYPE enum_tag_associations_entity_type AS ENUM ('library', 'bookshelf', 'book', 'block');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS tag_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    entity_type enum_tag_associations_entity_type NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'uq_tag_associations_tag_entity'
          AND table_schema = 'public'
          AND table_name = 'tag_associations'
    ) THEN
        ALTER TABLE tag_associations
            ADD CONSTRAINT uq_tag_associations_tag_entity
            UNIQUE (tag_id, entity_type, entity_id);
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS ix_tag_associations_entity
    ON tag_associations(entity_type, entity_id);

CREATE INDEX IF NOT EXISTS ix_tag_associations_tag
    ON tag_associations(tag_id);
