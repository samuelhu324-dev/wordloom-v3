-- 025_rebuild_chronicle_events.sql
-- Purpose: Align chronicle_events table with Plan40 minimal event store design
-- Strategy:
--   1. Drop legacy chronicle_events table (if exists) preserving clean schema
--   2. Recreate with new structure focusing on Book-centric events
--   3. Add indexes for frequent queries (by book + time, by event_type + time)
--   4. Default timestamps stored in UTC

BEGIN;

-- Drop legacy table; cascade removes dependent indexes
DROP TABLE IF EXISTS chronicle_events CASCADE;

CREATE TABLE chronicle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    block_id UUID NULL REFERENCES blocks(id) ON DELETE SET NULL,
    actor_id UUID NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now()),
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX idx_chronicle_events_book_time ON chronicle_events (book_id, occurred_at DESC);
CREATE INDEX idx_chronicle_events_type_time ON chronicle_events (event_type, occurred_at DESC);
CREATE INDEX idx_chronicle_events_created_at ON chronicle_events (created_at DESC);

COMMENT ON TABLE chronicle_events IS 'CHRONICLE-001: Minimal event store (Book-centric)';

COMMIT;
