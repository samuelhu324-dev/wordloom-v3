# ---- app/main.py (v4: /debug/dbinfo shows effective DATABASE_URL masked)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.database import SessionLocal
from urllib.parse import urlparse

app = FastAPI(title="Wordloom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers.loom import entries as loom_entries, sources as loom_sources, auth as loom_auth
app.include_router(loom_entries.router, prefix="/api/common", tags=["Common"])
app.include_router(loom_sources.router, prefix="/api/common", tags=["Common"])
app.include_router(loom_auth.router,    prefix="/api/common", tags=["Common"])

ORBIT_ENABLED = os.getenv("ORBIT_ENABLED", "false").lower() == "true"
if ORBIT_ENABLED:
    from app.routers.orbit import tasks as orbit_tasks, memos as orbit_memos, stats as orbit_stats
    app.include_router(orbit_tasks.router, prefix="/api/orbit", tags=["Orbit"])
    app.include_router(orbit_memos.router, prefix="/api/orbit", tags=["Orbit"])
    app.include_router(orbit_stats.router, prefix="/api/orbit", tags=["Orbit"])

@app.get("/debug/dbinfo")
def dbinfo():
    info = {}
    try:
        with SessionLocal() as s:
            db = s.execute(text("SELECT current_database()")).scalar()
            sp = s.execute(text("SHOW search_path")).scalar()
            exists = s.execute(text("SELECT to_regclass('public.entries') IS NOT NULL")).scalar()
            info["current_database"] = db
            info["search_path"] = sp
            info["has_public_entries"] = bool(exists)
    except Exception as e:
        info["error"] = str(e)

    # Show effective DATABASE_URL masked (driver://user:****@host:port/db)
    eff = os.getenv("DATABASE_URL", "")
    try:
        u = urlparse(eff)
        if u.scheme:
            masked = f"{u.scheme}://{u.username or ''}:****@{u.hostname or ''}:{u.port or ''}{u.path or ''}"
        else:
            masked = eff
    except Exception:
        masked = eff
    info["effective_DATABASE_URL"] = masked
    return info
