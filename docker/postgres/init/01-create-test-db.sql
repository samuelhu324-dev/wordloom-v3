-- DEVTEST-DB-5435
--
-- This file is executed by the official Postgres Docker entrypoint ONLY when the
-- data directory is initialized for the first time (i.e. when the volume is new).
--
-- It creates a dedicated test database in the same container.
--
-- Databases:
--   - wordloom_dev  (created via POSTGRES_DB)
--   - wordloom_test (created here)
--
SELECT 'CREATE DATABASE wordloom_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'wordloom_test')\gexec

-- -----------------------------------------------------------------------------
-- Environment sentinel (DEVTEST safety fuse)
--
-- Create a tiny metadata table in both DBs so API/worker can refuse to start
-- if they are pointed at the wrong database.
--
-- This runs only on first container init (new volume).
-- Migrations also create this table for existing DBs.
-- -----------------------------------------------------------------------------

\connect wordloom_dev

CREATE TABLE IF NOT EXISTS environment_sentinel (
	id integer PRIMARY KEY,
	project text NOT NULL,
	env text NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO environment_sentinel (id, project, env)
SELECT 1, 'wordloom', 'dev'
WHERE NOT EXISTS (SELECT 1 FROM environment_sentinel WHERE id = 1);

\connect wordloom_test

CREATE TABLE IF NOT EXISTS environment_sentinel (
	id integer PRIMARY KEY,
	project text NOT NULL,
	env text NOT NULL,
	created_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO environment_sentinel (id, project, env)
SELECT 1, 'wordloom', 'test'
WHERE NOT EXISTS (SELECT 1 FROM environment_sentinel WHERE id = 1);
