@echo off
setlocal
REM Activate venv if present
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM Ensure Python can import the local 'app' package
set PYTHONPATH=%CD%

REM Launch Loom API on port 8012 to avoid conflicts on 8000
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8012 --env-file .env
