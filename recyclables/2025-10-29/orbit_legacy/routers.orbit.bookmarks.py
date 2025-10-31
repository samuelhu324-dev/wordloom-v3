from __future__ import annotations
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database_orbit import get_orbit_db
from app.core.repo_orbit import list_bookmarks, create_bookmark, update_bookmark, delete_bookmark
from app.schemas.orbit.bookmarks import BookmarkCreate, BookmarkUpdate, BookmarkRead

router = APIRouter(prefix="/orbit/bookmarks", tags=["Orbit"])

@router.get("/health")
def health(): return {"router": "orbit.bookmarks", "ok": True}

@router.get("/", response_model=List[BookmarkRead])
def api_list_bookmarks(
    q: str = "",
    tag: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "-updated_at",
    limit: int = Query(100, le=500),
    db: Session = Depends(get_orbit_db),
):
    return list_bookmarks(db, q=q, tag=tag, status=status, sort=sort, limit=limit)

@router.post("/", response_model=BookmarkRead)
def api_create_bookmark(payload: BookmarkCreate, db: Session = Depends(get_orbit_db)):
    return create_bookmark(db, **payload.dict())

@router.put("/{id}", response_model=BookmarkRead)
def api_update_bookmark(id: str, payload: BookmarkUpdate, db: Session = Depends(get_orbit_db)):
    bm = update_bookmark(db, id, **payload.dict(exclude_unset=True))
    if not bm:
        raise HTTPException(404, "Bookmark not found")
    return bm

@router.delete("/{id}")
def api_delete_bookmark(id: str, db: Session = Depends(get_orbit_db)):
    ok = delete_bookmark(db, id)
    if not ok:
        raise HTTPException(404, "Bookmark not found")
    return {"ok": True}
