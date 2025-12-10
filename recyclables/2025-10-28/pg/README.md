# PostgreSQL toolbox (storage/pg)

PowerShell scripts to export and import PostgreSQL databases between a Docker container (running Postgres) and your local Postgres service.

## Layout
- `scripts/export.ps1` — Dump databases from Docker container into `backups/` as SQL files.
- `scripts/import.ps1` — Import latest dumps from `backups/` into local Postgres.
- `scripts/restore-from-storage.ps1` — Restore from `storage/wordloompg.sql` and `storage/wordloomorbit.sql` using `.env` connection.
- `backups/` — Output folder for `.sql` files (timestamped).

## Requirements
- Docker Desktop running and a container named `wordloompg` with Postgres.
- PostgreSQL client installed locally (`psql`, `createdb`) in PATH.

## Quick use

### Export from container
```powershell
# from repo root or any folder
& "D:\Project\Wordloom\WordloomBackend\api\storage\pg\scripts\export.ps1"
```
Options:
```powershell
& path\export.ps1 -Container wordloompg -User postgres -Databases @('wordloompg','wordloomorbit')
```

### Import into local Postgres
```powershell
# set password if needed
$env:PGPASSWORD = "your-local-password"
& "D:\Project\Wordloom\WordloomBackend\api\storage\pg\scripts\import.ps1" -DbHost localhost -User postgres
```

Use pgpass (no env var, non-interactive):
```powershell
& "D:\Project\Wordloom\WordloomBackend\api\storage\pg\scripts\import.ps1" -DbHost localhost -User postgres -UsePgPass -PgPassword "your-local-password"
```
This creates a temporary `pgpass` file (or use `-PgPassFile` to specify a path), sets `PGPASSFILE` for the process, runs import, then deletes the temp file.

### Import specific dump files (like storage/wordloompg.sql and storage/wordloomorbit.sql)
```powershell
& "D:\Project\Wordloom\WordloomBackend\api\storage\pg\scripts\import.ps1" `
	-UseEnv `
	-SqlFiles @(
		"D:\Project\Wordloom\WordloomBackend\api\storage\wordloompg.sql",
		"D:\Project\Wordloom\WordloomBackend\api\storage\wordloomorbit.sql"
	)
```
快捷方式：
```powershell
& "D:\Project\Wordloom\WordloomBackend\api\storage\pg\scripts\restore-from-storage.ps1"
```
Notes:
- `-UseEnv` makes the script read `.env` in `WordloomBackend/api/.env` and use the `DATABASE_URL` host/port/user/pass. If omitted, you can set `-DbHost/-Port/-User` or `$env:PGPASSWORD` manually.
- If you don't pass `-SqlFiles`, the script falls back to `backups/` (latest timestamped files per DB); if not found, it tries `storage/{db}.sql`.

## Notes
- Dumps are created with `--no-owner --no-privileges` for portability.
- If databases already exist locally and you want a clean import, drop and recreate them before running import.
- For very large databases, piping entire dump into memory may be slow; consider using direct shell redirection.
- Dumps and temporary pgpass files are ignored by `.gitignore` in this folder.
