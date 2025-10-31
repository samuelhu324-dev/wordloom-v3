"""
Orbit Bookshelf API Routes

端点：
- GET    /orbit/bookshelves              - 列出所有 Bookshelf
- POST   /orbit/bookshelves              - 创建新 Bookshelf
- GET    /orbit/bookshelves/{id}         - 获取 Bookshelf 详情
- PUT    /orbit/bookshelves/{id}         - 更新 Bookshelf
- DELETE /orbit/bookshelves/{id}         - 删除 Bookshelf
- POST   /orbit/bookshelves/{id}/notes   - 将 Note 加入 Bookshelf
- GET    /orbit/bookshelves/{id}/notes   - 列出 Bookshelf 内的 Notes
- DELETE /orbit/bookshelves/{id}/notes/{note_id} - 从 Bookshelf 移除 Note
- POST   /orbit/notes/{id}/move-to-bookshelf - 转移 Note 到另一个 Bookshelf
"""
from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session
from app.database_orbit import get_orbit_db
from app.models.orbit.bookshelves import OrbitBookshelf
from app.services.bookshelf_service import BookshelfService

router = APIRouter(prefix="/orbit", tags=["Orbit-Bookshelves"])

# ----- Schemas -----

class BookshelfOut(BaseModel):
    """Bookshelf 输出模型"""
    id: str
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    icon: Optional[str] = None
    priority: int = 3
    urgency: int = 3
    usage_count: int = 0
    note_count: int = 0
    status: str = "active"
    tags: List[str] = Field(default_factory=list)
    color: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True

class BookshelfIn(BaseModel):
    """Bookshelf 创建/更新请求体"""
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    icon: Optional[str] = None
    priority: Optional[int] = 3
    urgency: Optional[int] = 3
    tags: Optional[List[str]] = None
    color: Optional[str] = None
    is_favorite: Optional[bool] = False

class MoveNoteRequest(BaseModel):
    """转移 Note 的请求体"""
    target_bookshelf_id: str

# ----- Endpoints -----

@router.get("/bookshelves", response_model=List[BookshelfOut])
def list_bookshelves(
    status: str = Query("active", description="过滤状态: active, archived, deleted, all"),
    sort_by: str = Query("-created_at", description="排序字段"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_orbit_db),
):
    """列出所有 Bookshelves"""
    try:
        bookshelves = BookshelfService.list_bookshelves(
            status=status,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            db=db,
        )
        return bookshelves
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bookshelves", response_model=BookshelfOut)
def create_bookshelf(payload: BookshelfIn, db: Session = Depends(get_orbit_db)):
    """创建新 Bookshelf"""
    try:
        bs = BookshelfService.create_bookshelf(
            name=payload.name,
            description=payload.description,
            cover_url=payload.cover_url,
            icon=payload.icon,
            priority=payload.priority or 3,
            urgency=payload.urgency or 3,
            tags=payload.tags,
            color=payload.color,
            db=db,
        )
        return bs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bookshelves/{bookshelf_id}", response_model=BookshelfOut)
def get_bookshelf(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    """获取 Bookshelf 详情"""
    bs = BookshelfService.get_bookshelf(bookshelf_id, db)
    if not bs:
        raise HTTPException(status_code=404, detail="bookshelf not found")
    return bs

@router.put("/bookshelves/{bookshelf_id}", response_model=BookshelfOut)
def update_bookshelf(
    bookshelf_id: str,
    payload: BookshelfIn,
    db: Session = Depends(get_orbit_db),
):
    """更新 Bookshelf"""
    bs = BookshelfService.get_bookshelf(bookshelf_id, db)
    if not bs:
        raise HTTPException(status_code=404, detail="bookshelf not found")

    try:
        # 更新字段
        if payload.name:
            bs.name = payload.name
        if payload.description is not None:
            bs.description = payload.description
        if payload.cover_url is not None:
            bs.cover_url = payload.cover_url
        if payload.icon is not None:
            bs.icon = payload.icon
        if payload.priority is not None:
            bs.priority = payload.priority
        if payload.urgency is not None:
            bs.urgency = payload.urgency
        if payload.tags is not None:
            bs.tags = payload.tags
        if payload.color is not None:
            bs.color = payload.color
        if payload.is_favorite is not None:
            bs.is_favorite = payload.is_favorite

        bs.updated_at = datetime.utcnow()
        db.add(bs)
        db.commit()
        db.refresh(bs)
        return bs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bookshelves/{bookshelf_id}", status_code=204)
def delete_bookshelf(
    bookshelf_id: str,
    cascade: str = Query("orphan", description="删除策略: orphan (推荐) 或 delete"),
    db: Session = Depends(get_orbit_db),
):
    """删除 Bookshelf"""
    if cascade not in ("orphan", "delete"):
        raise HTTPException(status_code=400, detail="cascade must be 'orphan' or 'delete'")

    try:
        success = BookshelfService.delete_bookshelf(bookshelf_id, cascade=cascade, db=db)
        if not success:
            raise HTTPException(status_code=404, detail="bookshelf not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bookshelves/{bookshelf_id}/notes/{note_id}", response_model=dict)
def add_note_to_bookshelf(
    bookshelf_id: str,
    note_id: str,
    db: Session = Depends(get_orbit_db),
):
    """将 Note 添加到 Bookshelf"""
    try:
        note = BookshelfService.add_note_to_bookshelf(bookshelf_id, note_id, db)
        return {"success": True, "message": f"Note added to bookshelf", "note_id": str(note.id)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/bookshelves/{bookshelf_id}/notes/{note_id}", status_code=204)
def remove_note_from_bookshelf(
    bookshelf_id: str,
    note_id: str,
    db: Session = Depends(get_orbit_db),
):
    """从 Bookshelf 移除 Note（使其成为自由 Note）"""
    try:
        BookshelfService.remove_note_from_bookshelf(note_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bookshelves/{bookshelf_id}/notes", response_model=list)
def get_bookshelf_notes(
    bookshelf_id: str,
    sort_by: str = Query("-updated_at"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_orbit_db),
):
    """列出 Bookshelf 内的所有 Notes"""
    # 先检查 Bookshelf 是否存在
    bs = BookshelfService.get_bookshelf(bookshelf_id, db)
    if not bs:
        raise HTTPException(status_code=404, detail="bookshelf not found")

    try:
        from app.models.orbit.notes import OrbitNote
        notes = BookshelfService.get_bookshelf_notes(
            bookshelf_id,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
            db=db,
        )
        # 返回原始模型，前端会处理序列化
        return notes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notes/{note_id}/move-to-bookshelf", response_model=dict)
def move_note_to_bookshelf(
    note_id: str,
    payload: MoveNoteRequest,
    db: Session = Depends(get_orbit_db),
):
    """转移 Note 到另一个 Bookshelf"""
    try:
        note = BookshelfService.move_note_to_bookshelf(
            note_id,
            payload.target_bookshelf_id,
            db,
        )
        return {
            "success": True,
            "message": "Note moved to bookshelf",
            "note_id": str(note.id),
            "bookshelf_id": str(payload.target_bookshelf_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bookshelves/{bookshelf_id}/increment-usage", response_model=BookshelfOut)
def increment_bookshelf_usage(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    """增加 Bookshelf 的使用次数"""
    try:
        bs = BookshelfService.increment_usage_count(bookshelf_id, db)
        return bs
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
