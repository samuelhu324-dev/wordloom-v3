@echo off
setlocal
REM Activate venv if present
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM Ensure Python can import the local 'app' package
set PYTHONPATH=%CD%

REM Launch Orbit API on port 8011
python -m uvicorn app.main_orbit:app --reload --host 127.0.0.1 --port 8011 --env-file .env
