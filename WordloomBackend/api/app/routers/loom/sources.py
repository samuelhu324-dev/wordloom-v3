
# -*- coding: utf-8 -*-
from typing import List, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loom.sources import Source
from app.models.loom.entry_sources import EntrySource
from app.schemas.loom import RenameReq

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("", response_model=List[str])
@router.get("/", response_model=List[str])
def list_sources(db: Session = Depends(get_db)):
    rows_all = db.execute(select(Source.name)).all()
    rows_used = db.execute(
        select(Source.name)
        .select_from(Source)
        .join(EntrySource, EntrySource.source_id == Source.id)
        .distinct()
    ).all()

    names = set()
    for (n,) in rows_all:
        if n:
            names.add(n.strip())
    for (n,) in rows_used:
        if n:
            names.add(n.strip())
    return sorted(names)

def _count_usage(db: Session, name: str) -> Dict[str, int]:
    cnt_es = db.query(func.count())             .select_from(EntrySource)             .join(Source, EntrySource.source_id == Source.id)             .filter(Source.name == name).scalar() or 0
    return {"via_entry_sources": cnt_es, "total": cnt_es}

@router.post("/rename")
def rename_source(payload: RenameReq, db: Session = Depends(get_db)):
    src = db.execute(select(Source).where(Source.name == payload.from_name)).scalar_one_or_none()
    dst = db.execute(select(Source).where(Source.name == payload.to_name)).scalar_one_or_none()
    stat = _count_usage(db, payload.from_name)

    if payload.preview:
        return {"changed": 0, "details": stat, "note": "preview only"}

    if not src:
        return {"changed": 0, "details": stat, "note": "source(from) not found"}

    if dst is None:
        src.name = payload.to_name
        db.commit()
        return {"changed": stat["total"], "details": stat, "note": "renamed in-place"}

    db.execute(text("""
        DELETE FROM entry_sources es USING entry_sources es2
        WHERE es.entry_id = es2.entry_id
          AND es.source_id = :src AND es2.source_id = :dst
    """), {"src": src.id, "dst": dst.id})

    db.execute(text("UPDATE entry_sources SET source_id = :dst WHERE source_id = :src"),
               {"src": src.id, "dst": dst.id})

    db.delete(src)
    db.commit()
    return {"changed": stat["total"], "details": stat, "note": "merged into existing target"}
