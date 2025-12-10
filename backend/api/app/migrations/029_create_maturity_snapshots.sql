-- Create table for maturity snapshots (Plan_98)
CREATE TABLE IF NOT EXISTS maturity_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    stage VARCHAR(16) NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    components JSONB NOT NULL DEFAULT '[]'::jsonb,
    tasks JSONB NOT NULL DEFAULT '[]'::jsonb,
    signals JSONB NOT NULL DEFAULT '{}'::jsonb,
    manual_override BOOLEAN NOT NULL DEFAULT FALSE,
    manual_reason TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_maturity_snapshots_book_time
    ON maturity_snapshots (book_id, created_at DESC);
