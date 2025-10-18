# app/main.py (assets mount v2 - SAFE TWEAKS ONLY)
from pathlib import Path
import os
import logging

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles

from .database import engine
from .models import Base
from .routers import auth, entries, sources

Base.metadata.create_all(bind=engine)

def read_version():
    here = Path(__file__).resolve()
    backend_ver = here.parents[1] / "VERSION"
    root_ver    = here.parents[3] / "VERSION"   # 仓库根（.../Wordloom）
    vf = backend_ver if backend_ver.exists() else root_ver
    try:
        return vf.read_text(encoding="utf-8").strip()
    except Exception:
        return "unknown"

app = FastAPI(title="Wordloom API", version=read_version())

# ---------- CORS：默认允许本地前端，支持环境变量覆盖（无破坏） ----------
_default_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
_env_origins = os.getenv("CORS_ORIGINS", "").strip()
if _env_origins:
    allow_origins = [o.strip() for o in _env_origins.split(",") if o.strip()]
else:
    allow_origins = _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.getLogger("uvicorn.error").info(f"[CORS] allow_origins = {allow_origins}")

# 路由保持不变
app.include_router(auth.router)
app.include_router(entries.router)
app.include_router(sources.router)

# ---------- 静态挂载：/assets -> <repo root>/assets（无破坏） ----------
ROOT_DIR = Path(__file__).resolve().parents[3]
ASSETS_DIR = ROOT_DIR / "assets"
if ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR), html=False), name="assets")
    logging.getLogger(__name__).info(f"[STATIC] /assets -> {ASSETS_DIR}")
else:
    logging.getLogger(__name__).warning(f"[STATIC] assets directory not found: {ASSETS_DIR}")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/version")
def get_version():
    return {"backend": read_version()}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Wordloom API",
        version=read_version(),
        description="Wordloom 后端接口文档",
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path in openapi_schema.get("paths", {}).values():
        for method in path.values():
            method.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 维持你原有的 repo 绑定（无破坏）
from . import repo as _repo_module

@app.on_event("startup")
async def _bind_repo_to_state():
    app.state.repo = _repo_module
