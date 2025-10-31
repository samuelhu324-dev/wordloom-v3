from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pydantic import BaseModel
from typing import Optional, List, Union
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database_orbit import get_orbit_db, ORBIT_UPLOAD_DIR
import os
import uuid
import shutil

router = APIRouter(prefix="/orbit/memos", tags=["Orbit"])

TABLE = "memos"

class MemoCreate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[Union[List[str], str]] = None
    pinned: Optional[bool] = False
    image_url: Optional[str] = None

class MemoUpdate(BaseModel):
    title: Optional[str] = None
    text: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[Union[List[str], str]] = None
    pinned: Optional[bool] = None
    image_url: Optional[str] = None

def _norm_tags(v):
    if v is None: return None
    if isinstance(v, list): return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):  return [s.strip() for s in v.split(",") if s.strip()]
    return None

@router.get("", response_model=list)
@router.get("/", response_model=list)
def list_memos(q: str = "", limit: int = Query(50, le=500), offset: int = 0, db: Session = Depends(get_orbit_db)):
    sql = text(f"""
        select id::text, title, content, tags, pinned, ts, updated_at, image_url
        from {TABLE}
        where (:q = '' or title ilike :pat or content ilike :pat)
        order by ts desc
        limit :limit offset :offset
    """)
    rows = db.execute(sql, {"q": q, "pat": f"%{q}%", "limit": limit, "offset": offset}).all()
    return [
        {"id": r[0], "title": r[1], "text": r[2], "tags": r[3] or [], "pinned": r[4],
         "created_at": (r[5].isoformat() if hasattr(r[5], "isoformat") else r[5]),
         "updated_at": (r[6].isoformat() if hasattr(r[6], "isoformat") else r[6]),
         "image_url": r[7]}
        for r in rows
    ]

@router.post("", response_model=dict)
@router.post("/", response_model=dict)
def create_memo(payload: MemoCreate, db: Session = Depends(get_orbit_db)):
    content = payload.content or payload.text or ""
    tags = _norm_tags(payload.tags) or []
    row = db.execute(text(f"""
        insert into {TABLE} (title, content, tags, pinned, image_url)
        values (:title, :content, :tags, :pinned, :image_url)
        returning id::text, title, content, tags, pinned, ts, updated_at, image_url
    """), {"title": payload.title, "content": content, "tags": tags, "pinned": bool(payload.pinned), "image_url": payload.image_url}).fetchone()
    db.commit()
    return {"id": row[0], "title": row[1], "text": row[2], "tags": row[3] or [], "pinned": row[4],
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
            "image_url": row[7]}

# 从 _temp/ 移动图片到 memos/<memo_id>/ 并把最终 URL 写回 image_url
@router.post("/save-image")
async def save_image_to_memo(body: dict, db: Session = Depends(get_orbit_db)):
    memo_id = body.get("memo_id") or body.get("id")
    temp_url = body.get("temp_url") or body.get("url")
    if not memo_id or not temp_url:
        raise HTTPException(400, "missing memo_id or temp_url")

    after_static = temp_url.split("/api/orbit/static/")[-1]
    # 可能是 _temp/xxx.png 或完整路径，尽量解析到真实文件
    candidates = [
        os.path.join(ORBIT_UPLOAD_DIR, after_static),
        os.path.join(ORBIT_UPLOAD_DIR, "_temp", os.path.basename(after_static)),
    ]
    src = next((p for p in candidates if os.path.exists(p)), None)
    if not src:
        raise HTTPException(404, "temp file not found")

    dst_dir = os.path.join(ORBIT_UPLOAD_DIR, "memos", str(memo_id))
    os.makedirs(dst_dir, exist_ok=True)
    filename = os.path.basename(src)
    dst = os.path.join(dst_dir, filename)
    try:
        shutil.move(src, dst)
    except Exception:
        # 目标存在则覆盖后重试
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)

    backend = os.getenv("BACKEND_URL", "http://localhost:8000")
    final_url = f"{backend}/api/orbit/static/memos/{memo_id}/{filename}"

    row = db.execute(text(f"""
        update {TABLE}
        set image_url = :u, updated_at = now()
        where id = :id
        returning id::text, title, content, tags, pinned, ts, updated_at, image_url
    """), {"u": final_url, "id": memo_id}).fetchone()
    if not row: raise HTTPException(404, "memo not found")
    db.commit()
    return {"id": row[0], "title": row[1], "text": row[2], "tags": row[3] or [], "pinned": row[4],
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
            "image_url": row[7]}

# 便捷别名
@router.post("/{id}/save-image")
async def save_image_to_memo_by_id(id: str, body: dict, db: Session = Depends(get_orbit_db)):
    return await save_image_to_memo({"memo_id": id, "temp_url": body.get("temp_url") or body.get("url")}, db)

@router.put("/{id}", response_model=dict)
def update_memo(id: str, payload: MemoUpdate, db: Session = Depends(get_orbit_db)):
    content = (payload.content or payload.text) if (payload.content or payload.text) is not None else None
    tags = _norm_tags(payload.tags)
    row = db.execute(text(f"""
        update {TABLE} set
          title = coalesce(:title, title),
          content = coalesce(:content, content),
          tags = coalesce(:tags, tags),
          pinned = coalesce(:pinned, pinned),
          image_url = coalesce(:image_url, image_url),
          updated_at = now()
        where id = :id
        returning id::text, title, content, tags, pinned, ts, updated_at, image_url
    """), {"id": id, "title": payload.title, "content": content, "tags": tags, "pinned": payload.pinned, "image_url": payload.image_url}).fetchone()
    if not row: raise HTTPException(404, "memo not found")
    db.commit()
    return {"id": row[0], "title": row[1], "text": row[2], "tags": row[3] or [], "pinned": row[4],
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
            "image_url": row[7]}

@router.post("/{id}/clear-image")
def clear_image(id: str, db: Session = Depends(get_orbit_db)):
    row = db.execute(text(f"""
        update {TABLE}
        set image_url = NULL, updated_at = now()
        where id = :id
        returning id::text, title, content, tags, pinned, ts, updated_at, image_url
    """), {"id": id}).fetchone()
    if not row: raise HTTPException(404, "memo not found")
    db.commit()
    return {"id": row[0], "title": row[1], "text": row[2], "tags": row[3] or [], "pinned": row[4],
            "created_at": row[5].isoformat() if hasattr(row[5], "isoformat") else row[5],
            "updated_at": row[6].isoformat() if hasattr(row[6], "isoformat") else row[6],
            "image_url": row[7]}

@router.delete("/{id}")
def delete_memo(id: str, db: Session = Depends(get_orbit_db)):
    db.execute(text(f"delete from {TABLE} where id = :id"), {"id": id})
    db.commit()
    return {"ok": True}

@router.get("/health")
def health():
    return {"ok": True, "table": TABLE}

@router.get("/_db")
def dbinfo(db: Session = Depends(get_orbit_db)):
    out = {"table": TABLE}
    out["current_database"] = db.execute(text("select current_database()")).scalar()
    out["table_exists"] = bool(db.execute(text(f"select to_regclass('public.{TABLE}') is not null")).scalar())
    return out

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    temp_dir = os.path.join(ORBIT_UPLOAD_DIR, "_temp")
    os.makedirs(temp_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(temp_dir, name)
    with open(path, "wb") as f:
        f.write(await file.read())
    backend = os.getenv("BACKEND_URL", "http://localhost:8000")
    return {"url": f"{backend}/api/orbit/static/_temp/{name}"}



