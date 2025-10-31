@echo off
echo 打开 PowerShell，运行：
echo   $env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5432/wordloom"
echo   $env:DATABASE_URL_SQLITE = "sqlite:///app.db"
echo   python wordloom_pg_minimal\migrate_sqlite_to_pg_orm.py
pause
