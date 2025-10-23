@echo off
echo 打开 PowerShell，运行：
echo   $env:DATABASE_URL = "postgresql+psycopg://wordloom:wordloom@localhost:5432/wordloom"
echo   python wordloom_pg_minimal\init_pg_schema.py
pause
