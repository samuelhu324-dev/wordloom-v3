from __future__ import annotations
import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from urllib.parse import urlparse
from sqlalchemy import text

from app.database import SessionLocal

app = FastAPI(title="Wordloom Loom API")

origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 统一挂载到 /api/common 前缀下
api = APIRouter(prefix="/api/common")

from app.routers.loom import entries as loom_entries, sources as loom_sources, auth as loom_auth

# ✅ 挂载子路由（它们自己已有 /entries、/sources 前缀）
api.include_router(loom_entries.router, tags=["Loom-Entries"])
api.include_router(loom_sources.router, tags=["Loom-Sources"])
api.include_router(loom_auth.router, tags=["Loom-Auth"])

# ✅ 调试路由（保留）
@app.get("/debug/routes")
def debug_routes():
    return [{"path": r.path, "name": r.name, "methods": sorted(getattr(r, "methods", []))} for r in app.routes]

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

app.include_router(api)
