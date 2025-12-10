-- 024_add_books_maturity_column.sql
-- Introduces maturity lifecycle to books aggregate.
-- Adds books.maturity VARCHAR(16) with default 'seed' and normalizes existing rows.

BEGIN;

DO $$
BEGIN
    -- Add the maturity column when missing (idempotent for reruns)
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'books'
          AND column_name = 'maturity'
    ) THEN
        ALTER TABLE books ADD COLUMN maturity VARCHAR(16) NOT NULL DEFAULT 'seed';
    END IF;
END $$;

-- Ensure default aligns with new lifecycle baseline
ALTER TABLE books ALTER COLUMN maturity SET DEFAULT 'seed';

-- Normalize any pre-existing data (guards against invalid legacy values)
UPDATE books
SET maturity = 'seed'
WHERE maturity IS NULL
   OR TRIM(maturity) = ''
   OR LOWER(maturity) NOT IN ('seed', 'growing', 'stable', 'legacy');

DO $$
BEGIN
    -- Add check constraint only once; validate to enforce lifecycle values
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'books'
          AND constraint_name = 'books_maturity_check'
    ) THEN
        ALTER TABLE books
            ADD CONSTRAINT books_maturity_check
            CHECK (LOWER(maturity) IN ('seed', 'growing', 'stable', 'legacy'))
            NOT VALID;
    END IF;

    -- Validation step is safe to rerun; it becomes a no-op when already validated
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE table_name = 'books'
          AND constraint_name = 'books_maturity_check'
    ) THEN
        ALTER TABLE books VALIDATE CONSTRAINT books_maturity_check;
    END IF;
END $$;

COMMIT;
