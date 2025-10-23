# -*- coding: utf-8 -*-
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Path, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, text

from app.database import get_db
from app.models.loom.entries import Entry
from app.models.loom.sources import Source
from app.models.loom.entry_sources import EntrySource

router = APIRouter(prefix="/entries", tags=["entries"])

# ---------------- Pydantic ----------------
class EntryOut(BaseModel):
    id: int
    src: str = ""
    tgt: str = ""
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class EntryCreate(BaseModel):
    src: str
    tgt: str
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class EntryPatch(BaseModel):
    src: Optional[str] = None
    tgt: Optional[str] = None
    source_name: Optional[str] = None
    created_at: Optional[str] = None

class BatchItem(BaseModel):
    text: str
    translation: Optional[str] = None
    direction: str                # "en>zh" | "zh>en"
    source_name: Optional[str] = None
    ts_iso: Optional[str] = None

class BatchCreate(BaseModel):
    items: List[BatchItem]

# ---------------- helpers ----------------
def _row_to_out(e: Entry, source_name: Optional[str]) -> Dict[str, Any]:
    return {
        "id": e.id,
        "src": getattr(e, "src_text", "") or "",
        "tgt": getattr(e, "tgt_text", "") or "",
        "source_name": source_name or None,
        "created_at": e.created_at.isoformat() if getattr(e, "created_at", None) else None,
    }

def _ensure_source(db: Session, name: Optional[str]) -> Optional[Source]:
    if not name:
        return None
    obj = db.execute(select(Source).where(Source.name == name)).scalar_one_or_none()
    if not obj:
        obj = Source(name=name)
        db.add(obj)
        db.flush()
    return obj

def _link_source(db: Session, entry_id: int, source_obj: Optional[Source]):
    # 覆盖式：先清旧关联，再添加
    db.query(EntrySource).filter_by(entry_id=entry_id).delete()
    if source_obj:
        db.add(EntrySource(entry_id=entry_id, source_id=source_obj.id))

def _parse_dt(iso: Optional[str]) -> Optional[datetime]:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(iso)
    except Exception:
        return None

# 仅通过 entry_sources → sources 解析来源（与 articles 完全解耦）
def _resolve_source_name_map(db: Session, entry_ids: List[int]) -> Dict[int, Optional[str]]:
    if not entry_ids:
        return {}
    name_map: Dict[int, Optional[str]] = {}
    q = (
        select(EntrySource.entry_id, Source.name)
        .join(Source, EntrySource.source_id == Source.id)
        .where(EntrySource.entry_id.in_(entry_ids))
    )
    for eid, sname in db.execute(q).all():
        if eid not in name_map:
            name_map[eid] = sname
    return name_map

# ---------------- READ ----------------
@router.get("/search")
def search_entries(
    # 兼容两种参数名：q（新）与 keyword（旧）
    q: Optional[str] = Query(None, description="search keyword"),
    keyword: Optional[str] = Query(None, alias="keyword"),
    source_name: Optional[str] = Query(None),
    limit: int = 1000,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    term = (q if q is not None else keyword) or ""
    term = term.strip()

    stmt = select(Entry).distinct()

    if term:
        like = f"%{term}%"
        stmt = stmt.where(or_(Entry.src_text.ilike(like), Entry.tgt_text.ilike(like)))

    if source_name:
        stmt = (
            stmt.join(EntrySource, Entry.id == EntrySource.entry_id)
                .join(Source, EntrySource.source_id == Source.id)
                .where(Source.name == source_name)
        )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    rows = db.execute(
        stmt.order_by(Entry.created_at.desc().nullslast(), Entry.id.desc())
            .limit(limit).offset(offset)
    ).scalars().all()

    ids = [e.id for e in rows]
    name_map = _resolve_source_name_map(db, ids)
    items = [_row_to_out(e, name_map.get(e.id)) for e in rows]
    return {"items": items, "total": total}

@router.get("/{entry_id}", response_model=EntryOut)
def read_entry(entry_id: int = Path(..., ge=1), db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e:
        raise HTTPException(404, "entry not found")
    sname = _resolve_source_name_map(db, [entry_id]).get(entry_id)
    return EntryOut(**_row_to_out(e, sname))

# ---------------- CREATE ----------------
@router.post("")
def create_entry(payload: EntryCreate, db: Session = Depends(get_db)):
    e = Entry(
        src_text=payload.src.strip(),
        tgt_text=payload.tgt.strip(),
        created_at=_parse_dt(payload.created_at),
    )
    db.add(e); db.flush()
    src_obj = _ensure_source(db, payload.source_name)
    _link_source(db, e.id, src_obj)
    db.commit()
    sname = src_obj.name if src_obj else None
    return EntryOut(**_row_to_out(e, sname))

@router.post("/batch")
def create_batch(batch: BatchCreate, db: Session = Depends(get_db)):
    created = 0
    for it in batch.items:
        is_en2zh = (it.direction or "").lower() in ("en>zh", "en-zh", "en2zh")
        src = it.text if is_en2zh else (it.translation or "")
        tgt = (it.translation or "") if is_en2zh else it.text
        if not (src or tgt):
            continue
        e = Entry(
            src_text=src.strip(),
            tgt_text=tgt.strip(),
            created_at=_parse_dt(it.ts_iso),
        )
        db.add(e); db.flush()
        src_obj = _ensure_source(db, it.source_name)
        _link_source(db, e.id, src_obj)
        created += 1
    db.commit()
    return {"created": created}

# ---------------- UPDATE ----------------
@router.patch("/{entry_id}")
@router.put("/{entry_id}")
def update_entry(entry_id: int, patch: EntryPatch, db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e:
        raise HTTPException(404, "entry not found")

    if patch.src is not None:
        e.src_text = patch.src.strip()
    if patch.tgt is not None:
        e.tgt_text = patch.tgt.strip()
    if patch.created_at is not None:
        dt = _parse_dt(patch.created_at)
        if dt:
            e.created_at = dt
    if patch.source_name is not None:
        src_obj = _ensure_source(db, patch.source_name)
        _link_source(db, entry_id, src_obj)

    db.commit()
    sname = _resolve_source_name_map(db, [entry_id]).get(entry_id)
    return EntryOut(**_row_to_out(e, sname))

# 兼容旧路径：POST /entries/update
@router.post("/update")
def update_entry_legacy(
    id: int = Body(..., embed=True),
    src: Optional[str] = Body(None),
    tgt: Optional[str] = Body(None),
    source_name: Optional[str] = Body(None),
    created_at: Optional[str] = Body(None),
    db: Session = Depends(get_db),
):
    patch = EntryPatch(src=src, tgt=tgt, source_name=source_name, created_at=created_at)
    return update_entry(id, patch, db)

# ---------------- DELETE ----------------
@router.delete("/{entry_id}")
def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    e = db.get(Entry, entry_id)
    if not e:
        raise HTTPException(404, "entry not found")
    db.query(EntrySource).filter_by(entry_id=entry_id).delete()
    db.delete(e)
    db.commit()
    return {"status": "deleted", "id": entry_id}

# 兼容旧路径：POST /entries/delete
@router.post("/delete")
def delete_entry_legacy(id: int = Body(..., embed=True), db: Session = Depends(get_db)):
    return delete_entry(id, db)

# ---------------- UTIL: 批量为词条打来源 ----------------
class AssignSourceReq(BaseModel):
    source_name: str
    entry_ids: Optional[List[int]] = None   # 不传则作用于所有“未关联”的词条
    only_unlinked: bool = True              # True: 仅未关联；False: 覆盖式重打

@router.post("/assign-source")
def assign_source(req: AssignSourceReq, db: Session = Depends(get_db)):
    src_obj = _ensure_source(db, req.source_name)
    if not src_obj:
        raise HTTPException(400, "source_name is required")

    sid = src_obj.id
    changed = 0

    if req.entry_ids:
        ids = [int(i) for i in req.entry_ids if i is not None]
        if not ids:
            return {"changed": 0, "source": req.source_name}

        if req.only_unlinked:
            db.execute(
                text("""
                    INSERT INTO entry_sources (entry_id, source_id)
                    SELECT e.id, :sid
                    FROM entries e
                    LEFT JOIN entry_sources es ON es.entry_id = e.id
                    WHERE e.id = ANY(:ids) AND es.entry_id IS NULL
                """),
                {"sid": sid, "ids": ids},
            )
        else:
            db.execute(text("DELETE FROM entry_sources WHERE entry_id = ANY(:ids)"),
                       {"ids": ids})
            db.execute(
                text("""
                    INSERT INTO entry_sources (entry_id, source_id)
                    SELECT UNNEST(:ids), :sid
                """),
                {"ids": ids, "sid": sid},
            )
        changed = len(ids)
    else:
        res = db.execute(
            text("""
                INSERT INTO entry_sources (entry_id, source_id)
                SELECT e.id, :sid
                FROM entries e
                LEFT JOIN entry_sources es ON es.entry_id = e.id
                WHERE es.entry_id IS NULL
                RETURNING entry_id
            """),
            {"sid": sid},
        )
        changed = len(res.fetchall())

    db.commit()
    return {"changed": changed, "source": req.source_name}
