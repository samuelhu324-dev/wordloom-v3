from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.entries import router as entries_router
from app.routers.sources import router as sources_router
from app.routers.auth import router as auth_router

# Orbit routers
from app.routers.orbit_tasks import router as orbit_tasks_router
from app.routers.orbit_memos import router as orbit_memos_router
from app.routers.orbit_stats import router as orbit_stats_router

app = FastAPI(title="Wordloom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

# original
app.include_router(auth_router)
app.include_router(entries_router)
app.include_router(sources_router)

# orbit
app.include_router(orbit_tasks_router)
app.include_router(orbit_memos_router)
app.include_router(orbit_stats_router)

# dual-track /api
app.include_router(auth_router, prefix="/api")
app.include_router(entries_router, prefix="/api")
app.include_router(sources_router, prefix="/api")
app.include_router(orbit_tasks_router, prefix="/api")
app.include_router(orbit_memos_router, prefix="/api")
app.include_router(orbit_stats_router, prefix="/api")

@app.get("/")
def home():
    return {"message": "Wordloom API is running with Orbit module enabled!"}

# ensure table creation
import app.models_orbit  # noqa: F401
