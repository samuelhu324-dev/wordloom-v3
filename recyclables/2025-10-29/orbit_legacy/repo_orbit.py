from __future__ import annotations
import uuid
from typing import List, Optional
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import Session
from app.models.orbit import Bookmark

def _to_uuid(v):
    if isinstance(v, uuid.UUID):
        return v
    try:
        return uuid.UUID(str(v))
    except Exception:
        return None

def list_bookmarks(
    db: Session,
    q: str = "",
    tag: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "-updated_at",
    limit: int = 100,
    offset: int = 0,
) -> List[Bookmark]:
    try:
        stmt = select(Bookmark)

        if q:
            q_like = f"%{q}%"
            stmt = stmt.where(or_(Bookmark.title.ilike(q_like), Bookmark.text.ilike(q_like)))

        if tag:
            stmt = stmt.where(Bookmark.tags.any(tag))

        if status:
            stmt = stmt.where(Bookmark.status == status)

        desc_order = sort.startswith("-")
        field = sort[1:] if desc_order else sort
        order_col = getattr(Bookmark, field, None) or getattr(Bookmark, "created_at")
        stmt = stmt.order_by(desc(order_col) if desc_order else order_col)

        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        result = list(db.execute(stmt).scalars().all())
        return result
    except Exception as e:
        print(f"[repo_orbit.list_bookmarks] Error: {e}")
        raise

def create_bookmark(db: Session, **data) -> Bookmark:
    obj = Bookmark(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_bookmark(db: Session, id, **data) -> Optional[Bookmark]:
    uid = _to_uuid(id)
    obj = db.get(Bookmark, uid) if uid else None
    if not obj:
        return None
    for k, v in data.items():
        if v is not None and hasattr(obj, k):
            setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

def delete_bookmark(db: Session, id) -> bool:
    uid = _to_uuid(id)
    obj = db.get(Bookmark, uid) if uid else None
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True

def get_stats(db: Session, days: int = 7) -> dict:
    total = db.scalar(select(func.count()).select_from(Bookmark)) or 0
    return {"total": total, "days": days}
