# -*- coding: utf-8 -*-
# app/routers/loom/entries.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Path, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database import get_db
from app.models.loom.entries import Entry
from app.models.loom.sources import Source
from app.models.loom.entry_sources import EntrySource

router = APIRouter(prefix="/entries", tags=["entries"])

class EntryOut(BaseModel):
    id: int
    src: str = ""
    tgt: str = ""
    source_name: Optional[str] = None
    created_at: Optional[str] = None

def _row_to_out(e: Entry, source_name: Optional[str]) -> Dict[str, Any]:
    return {
        "id": e.id,
        "src": getattr(e, "src_text", "") or "",
        "tgt": getattr(e, "tgt_text", "") or "",
        "source_name": source_name or None,
        "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None,
    }

@router.get("/search")
def search_entries(
    source_name: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    stmt = select(Entry)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Entry.src_text.ilike(like)) | (Entry.tgt_text.ilike(like)))
    if source_name:
        stmt = (
            stmt.join(EntrySource, Entry.id == EntrySource.entry_id)
               .join(Source, EntrySource.source_id == Source.id)
               .where(Source.name == source_name)
        )
    # total
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    stmt = stmt.order_by(Entry.created_at.desc().nullslast()).limit(limit).offset(offset)
    entries = db.execute(stmt).scalars().all()

    # source map
    entry_ids = [e.id for e in entries]
    name_map: Dict[int, Optional[str]] = {}
    if entry_ids:
        join_stmt = (
            select(EntrySource.entry_id, Source.name)
            .join(Source, EntrySource.source_id == Source.id)
            .where(EntrySource.entry_id.in_(entry_ids))
        )
        for eid, sname in db.execute(join_stmt).all():
            name_map[eid] = sname

    items = [_row_to_out(e, name_map.get(e.id)) for e in entries]
    return {"items": items, "total": total}

@router.get("/{entry_id}", response_model=EntryOut)
def read_entry(entry_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e:
        raise HTTPException(404, "entry not found")
    sname = db.execute(
        select(Source.name)
        .join(EntrySource, EntrySource.source_id == Source.id)
        .where(EntrySource.entry_id == entry_id)
        .limit(1)
    ).scalar()
    return EntryOut(**_row_to_out(e, sname))
