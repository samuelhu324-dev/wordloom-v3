from __future__ import annotations
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database_orbit import ORBIT_UPLOAD_DIR, ensure_orbit_dirs, ensure_orbit_extensions, ensure_orbit_tables
from app.routers.orbit import notes as orbit_notes
from app.routers.orbit import uploads as orbit_uploads
from app.routers.orbit import tags as orbit_tags
from app.routers.orbit import diagrams as orbit_diagrams
from app.routers.orbit import bookshelves as orbit_bookshelves

app = FastAPI(title="Wordloom Orbit API")
api = APIRouter(prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_orbit_dirs()
ensure_orbit_extensions()
ensure_orbit_tables()  # 新增
app.mount("/uploads", StaticFiles(directory=ORBIT_UPLOAD_DIR), name="uploads")

api.include_router(orbit_notes.router)
api.include_router(orbit_uploads.router)
api.include_router(orbit_tags.router)
api.include_router(orbit_diagrams.router)
api.include_router(orbit_bookshelves.router)
app.include_router(api)