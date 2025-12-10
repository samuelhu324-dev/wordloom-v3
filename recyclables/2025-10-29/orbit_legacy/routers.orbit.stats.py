from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database_orbit import get_orbit_db
from app.core.repo_orbit import get_stats

router = APIRouter(prefix="/orbit/stats", tags=["Orbit"])

@router.get("/health")
def health():
    return {"router": "orbit.stats", "ok": True}

@router.get("")
@router.get("/")
def summary(db: Session = Depends(get_orbit_db)):
    return get_stats(db)
