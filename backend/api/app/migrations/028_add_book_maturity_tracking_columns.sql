-- 028_add_book_maturity_tracking_columns.sql
-- Adds maturity telemetry columns required by Plan92 / POLICY-BOOK-MATURITY-* rules
-- Columns: maturity_score, legacy_flag, manual_maturity_override, manual_maturity_reason,
--          last_visited_at, visit_count_90d
--
-- This script is idempotent: every ALTER is wrapped with a metadata check so
-- repeated executions (or partially applied deployments) remain safe.

BEGIN;

-- maturity_score (INT NOT NULL DEFAULT 0)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'maturity_score'
    ) THEN
        ALTER TABLE books
            ADD COLUMN maturity_score INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- legacy_flag (BOOLEAN NOT NULL DEFAULT FALSE)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'legacy_flag'
    ) THEN
        ALTER TABLE books
            ADD COLUMN legacy_flag BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- manual_maturity_override (BOOLEAN NOT NULL DEFAULT FALSE)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'manual_maturity_override'
    ) THEN
        ALTER TABLE books
            ADD COLUMN manual_maturity_override BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- manual_maturity_reason (TEXT NULL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'manual_maturity_reason'
    ) THEN
        ALTER TABLE books
            ADD COLUMN manual_maturity_reason TEXT NULL;
    END IF;
END $$;

-- last_visited_at (TIMESTAMP WITH TIME ZONE NULL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'last_visited_at'
    ) THEN
        ALTER TABLE books
            ADD COLUMN last_visited_at TIMESTAMP WITH TIME ZONE NULL;
    END IF;
END $$;

-- visit_count_90d (INT NOT NULL DEFAULT 0)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books' AND column_name = 'visit_count_90d'
    ) THEN
        ALTER TABLE books
            ADD COLUMN visit_count_90d INTEGER NOT NULL DEFAULT 0;
    END IF;
END $$;

-- Backfill: ensure NULLs are replaced with defaults if columns pre-existed but were nullable
UPDATE books
SET
    maturity_score = COALESCE(maturity_score, 0),
    legacy_flag = COALESCE(legacy_flag, FALSE),
    manual_maturity_override = COALESCE(manual_maturity_override, FALSE),
    visit_count_90d = COALESCE(visit_count_90d, 0)
WHERE
    maturity_score IS NULL
    OR legacy_flag IS NULL
    OR manual_maturity_override IS NULL
    OR visit_count_90d IS NULL;

COMMIT;
