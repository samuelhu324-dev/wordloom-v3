# -*- coding: utf-8 -*-
from typing import List, Dict
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.loom.sources import Source
from app.models.loom.entry_sources import EntrySource

router = APIRouter(prefix="/sources", tags=["sources"])

# 兼容 /sources 与 /sources/ 两种写法；只依赖 sources/entry_sources
@router.get("", response_model=List[str])
@router.get("/", response_model=List[str])
def list_sources(db: Session = Depends(get_db)):
    # ① 所有在 sources 表登记过的名称（即便未被使用也返回，供下拉提示）
    rows_all = db.execute(select(Source.name)).all()
    # ② 已被 entry_sources 使用到的名称（去重）
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

# ---------- 重命名（带 preview，目标存在时安全合并） ----------
class RenameReq(BaseModel):
    from_name: str
    to_name: str
    preview: bool = True

def _count_usage(db: Session, name: str) -> Dict[str, int]:
    cnt_es = db.query(func.count()) \
        .select_from(EntrySource) \
        .join(Source, EntrySource.source_id == Source.id) \
        .filter(Source.name == name).scalar() or 0
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

    # 目标已存在：迁移 entry_sources 引用，避免 (entry_id, source_id) 冲突
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
