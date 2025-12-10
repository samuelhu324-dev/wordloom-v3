-- Migration 019: Allow tag associations with Libraries (Plan_31 Tag Row)
-- Adds 'library' value to enum used by tag_associations.entity_type so
-- frontend Library cards can fetch real tags directly from PostgreSQL.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_type t
        WHERE t.typname = 'enum_tag_associations_entity_type'
    ) THEN
        RAISE EXCEPTION 'enum_tag_associations_entity_type does not exist. Apply base schema first.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_enum e
        JOIN pg_type t ON e.enumtypid = t.oid
        WHERE t.typname = 'enum_tag_associations_entity_type'
          AND e.enumlabel = 'library'
    ) THEN
        ALTER TYPE enum_tag_associations_entity_type ADD VALUE 'library';
    END IF;
END$$;
