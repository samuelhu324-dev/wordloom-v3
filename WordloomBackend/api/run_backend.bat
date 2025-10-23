@echo off
setlocal
REM === Activate local venv if present ===
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
)

REM === Launch FastAPI app ===
REM NOTE: module path is app.main:app (NOT backend.app.main:app)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
