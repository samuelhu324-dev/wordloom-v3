# -*- coding: utf-8 -*-
"""
entries.py —— 扩展版（向后兼容）
- 保留 /entries/search
- 新增：GET /entries/{id}、PATCH/PUT /entries/{id}、DELETE /entries/{id}
- 兼容 repo 风格（优先调用 repo 上的方法；缺少则用 SQL 兜底）
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Request, Path, Body
from pydantic import BaseModel

router = APIRouter(prefix="/entries", tags=["entries"])

def _get_repo(request: Request):
    rep = getattr(request.app.state, "repo", None)
    if rep is not None:
        return rep
    try:
        from .. import repo as rep
        return rep
    except Exception:
        return None

class EntryOut(BaseModel):
    id: int
    src: str = ""
    tgt: str = ""
    source_name: Optional[str] = None
    created_at: Optional[str] = None

def _row_to_out(row: Any) -> Dict[str, Any]:
    if isinstance(row, dict):
        return {"id": row.get("id"),
                "src": row.get("src") or row.get("src_text") or row.get("text") or "",
                "tgt": row.get("tgt") or row.get("tgt_text") or row.get("translation") or "",
                "source_name": row.get("source_name") or row.get("source") or "",
                "created_at": str(row.get("created_at") or "")}
    try:
        return {"id": row[0], "src": row[1], "tgt": row[2], "source_name": row[3], "created_at": str(row[4])}
    except Exception:
        return {"id": -1, "src": "", "tgt": "", "source_name": "", "created_at": ""}

@router.get("/search")
def search_entries(
    request: Request,
    source_name: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = 1000,
    offset: int = 0,
):
    repo = _get_repo(request)
    if not repo:
        return {"items": [], "total": 0}

    if source_name and not q:
        rows = repo.search(q=None, source_names=[source_name], limit=limit, offset=offset)
    else:
        rows = repo.search(q=q or "", source_names=([source_name] if source_name else None), limit=limit, offset=offset)

    items = [EntryOut(**_row_to_out(r)) for r in rows]
    return {"items": items, "total": len(items)}

# ===== 新增：按 id 读取 =====
@router.get("/{entry_id}", response_model=EntryOut)
def read_entry(request: Request, entry_id: int = Path(..., ge=1)):
    repo = _get_repo(request)
    if not repo:
        raise HTTPException(500, "repo not available")
    # 优先调用 repo 方法
    if hasattr(repo, "get_by_id"):
        row = repo.get_by_id(entry_id)
    elif hasattr(repo, "get"):
        row = repo.get(entry_id)
    else:
        # 兜底：尝试通用查询
        rows = repo.search(q=None, ids=[entry_id], limit=1, offset=0) if hasattr(repo, "search") else []
        row = rows[0] if rows else None
    if not row:
        raise HTTPException(404, "entry not found")
    return EntryOut(**_row_to_out(row))

# ===== 新增：更新（PATCH/PUT） =====
class EntryPatch(BaseModel):
    src: Optional[str] = None
    tgt: Optional[str] = None
    source_name: Optional[str] = None

@router.patch("/{entry_id}")
@router.put("/{entry_id}")
def update_entry(request: Request, entry_id: int, patch: EntryPatch):
    repo = _get_repo(request)
    if not repo:
        raise HTTPException(500, "repo not available")

    ok = False
    # 尝试 repo 方法
    for name in ("update_entry", "update", "edit"):
        if hasattr(repo, name):
            try:
                getattr(repo, name)(entry_id, src=patch.src, tgt=patch.tgt, source_name=patch.source_name)
                ok = True
                break
            except TypeError:
                # 形参名不同，尝试常见别名
                try:
                    getattr(repo, name)(entry_id, text=patch.src, translation=patch.tgt, source_name=patch.source_name)
                    ok = True
                    break
                except Exception:
                    pass
            except Exception:
                pass

    if not ok and hasattr(repo, "execute"):
        # 兜底 SQL（SQLite）
        sets, params = [], {"id": entry_id}
        if patch.src is not None:
            sets.append("src = :src"); params["src"] = patch.src
            sets.append("text = :src")
        if patch.tgt is not None:
            sets.append("tgt = :tgt"); params["tgt"] = patch.tgt
            sets.append("translation = :tgt")
        if patch.source_name is not None:
            sets.append("source_name = :sn"); params["sn"] = patch.source_name
        if sets:
            repo.execute(f"UPDATE entries SET {', '.join(sets)} WHERE id = :id", params)
            ok = True

    if not ok:
        raise HTTPException(400, "update not supported by repo")

    # 返回最新
    try:
        return read_entry(request, entry_id)
    except Exception:
        return {"status": "ok", "id": entry_id}

# ===== 新增：删除 =====
@router.delete("/{entry_id}")
def delete_entry(request: Request, entry_id: int):
    repo = _get_repo(request)
    if not repo:
        raise HTTPException(500, "repo not available")

    ok = False
    for name in ("delete_entry","delete","remove"):
        if hasattr(repo, name):
            try:
                getattr(repo, name)(entry_id)
                ok = True; break
            except Exception: pass

    if not ok and hasattr(repo, "execute"):
        repo.execute("DELETE FROM entries WHERE id = :id", {"id": entry_id})
        ok = True

    if not ok:
        raise HTTPException(400, "delete not supported by repo")
    return {"status":"deleted","id":entry_id}
