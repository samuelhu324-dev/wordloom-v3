r"""Windows launcher for the Wordloom API.

Why this exists:
- psycopg async cannot run on Windows ProactorEventLoop.
- When launching uvicorn normally on Windows, the event loop may be Proactor.

This script forces a SelectorEventLoop via asyncio.run(loop_factory=...).

Usage (PowerShell, from repo root):
  $env:WORDLOOM_ENV = 'test'
  $env:DATABASE_URL = 'postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'
  $env:WORDLOOM_TRACING_ENABLED = '1'
  $env:OTEL_TRACES_SAMPLER = 'always_on'
  $env:OTEL_EXPORTER_OTLP_ENDPOINT = 'http://localhost:4318'

    .\.venv\Scripts\python.exe .\backend\scripts\run_api_win.py
"""

from __future__ import annotations

import asyncio
import os
import selectors
import sys
from pathlib import Path

import uvicorn


def _loop_factory() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


async def _serve() -> None:
    config = uvicorn.Config(
        "api.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    here = Path(__file__).resolve()
    backend_root = here.parents[1]

    # Make `api.*` importable when launching from repo root.
    os.chdir(backend_root)
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    asyncio.run(_serve(), loop_factory=_loop_factory)


if __name__ == "__main__":
    main()
