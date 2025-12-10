from __future__ import annotations
from typing import Optional, List, Any
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer, ConfigDict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, asc
from app.database_orbit import get_orbit_db, ORBIT_UPLOAD_DIR
from app.models.orbit.bookshelves import OrbitBookshelf
from app.models.orbit.notes import OrbitNote
from app.core.storage_manager import StorageManager
from app.routers.orbit.notes import NoteOut, BookshelfTagInfo, extract_first_image, extract_preview_text

router = APIRouter(prefix="/orbit", tags=["Orbit-Bookshelves"])
storage_mgr = StorageManager(ORBIT_UPLOAD_DIR)

class BookshelfOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, ser_json_timedelta='float')

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
    tags: list = Field(default_factory=list)
    color: Optional[str] = None
    is_favorite: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_serializer("created_at", "updated_at", mode='plain')
    def serialize_dt(self, value: Any) -> Optional[str]:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, str):
            return value
        return None

class BookshelfIn(BaseModel):
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    icon: Optional[str] = None
    priority: Optional[int] = 3
    urgency: Optional[int] = 3
    tags: Optional[list] = None
    color: Optional[str] = None
    is_favorite: Optional[bool] = False

class MoveNoteRequest(BaseModel):
    target_bookshelf_id: str

@router.get("/bookshelves", response_model=List[BookshelfOut])
def list_bookshelves(status: str = Query("active"), sort_by: str = Query("-created_at"), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_orbit_db)):
    try:
        stmt = select(OrbitBookshelf)
        if status != "all":
            stmt = stmt.where(OrbitBookshelf.status == status)
        if sort_by == "-created_at":
            stmt = stmt.order_by(desc(OrbitBookshelf.created_at))
        else:
            stmt = stmt.order_by(desc(OrbitBookshelf.created_at))
        stmt = stmt.limit(limit).offset(offset)
        results = db.execute(stmt).scalars().all()

        # Convert to dicts for proper serialization
        output = []
        for bs in results:
            output.append({
                "id": bs.id,
                "name": bs.name,
                "description": bs.description,
                "cover_url": bs.cover_url,
                "icon": bs.icon,
                "priority": bs.priority,
                "urgency": bs.urgency,
                "usage_count": bs.usage_count,
                "note_count": bs.note_count,
                "status": bs.status,
                "tags": bs.tags,
                "color": bs.color,
                "is_favorite": bs.is_favorite,
                "is_pinned": bs.is_pinned,
                "pinned_at": bs.pinned_at.isoformat() if bs.pinned_at else None,
                "created_at": bs.created_at.isoformat() if bs.created_at else None,
                "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
            })
        return output
    except Exception as e:
        print(f"List error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bookshelves", response_model=BookshelfOut)
def create_bookshelf(payload: BookshelfIn, db: Session = Depends(get_orbit_db)):
    """
    创建书架

    业界标准方案（固定存储路径）:
    - 创建 DB 记录
    - 创建文件夹结构 storage/bookshelves/{bookshelf_id}/（用于存储封面图）
    - 笔记文件始终存储在 storage/notes/{note_id}/
    """
    try:
        if not payload.name or not payload.name.strip():
            raise HTTPException(status_code=400, detail="Name required")
        bs_id = str(uuid4())
        bs = OrbitBookshelf(
            id=bs_id,
            name=payload.name.strip(),
            description=payload.description or "",
            cover_url=payload.cover_url,
            icon=payload.icon,
            priority=payload.priority or 3,
            urgency=payload.urgency or 3,
            tags=payload.tags or [],
            color=payload.color,
            is_favorite=payload.is_favorite or False,
            status="active",
            note_count=0,
            usage_count=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(bs)
        db.commit()
        db.refresh(bs)

        # 创建书架的存储文件夹
        storage_mgr.create_bookshelf_storage(bs_id)

        print(f"[BOOKSHELF] Created {bs.name} with storage folder")

        return {
            "id": bs.id,
            "name": bs.name,
            "description": bs.description,
            "cover_url": bs.cover_url,
            "icon": bs.icon,
            "priority": bs.priority,
            "urgency": bs.urgency,
            "usage_count": bs.usage_count,
            "note_count": bs.note_count,
            "status": bs.status,
            "tags": bs.tags,
            "color": bs.color,
            "is_favorite": bs.is_favorite,
            "is_pinned": bs.is_pinned,
            "pinned_at": bs.pinned_at.isoformat() if bs.pinned_at else None,
            "created_at": bs.created_at.isoformat() if bs.created_at else None,
            "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Create bookshelf failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bookshelves/{bookshelf_id}", response_model=BookshelfOut)
def get_bookshelf(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": bs.id,
        "name": bs.name,
        "description": bs.description,
        "cover_url": bs.cover_url,
        "icon": bs.icon,
        "priority": bs.priority,
        "urgency": bs.urgency,
        "usage_count": bs.usage_count,
        "note_count": bs.note_count,
        "status": bs.status,
        "tags": bs.tags,
        "color": bs.color,
        "is_favorite": bs.is_favorite,
        "created_at": bs.created_at.isoformat() if bs.created_at else None,
        "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
    }

@router.put("/bookshelves/{bookshelf_id}", response_model=BookshelfOut)
def update_bookshelf(bookshelf_id: str, payload: BookshelfIn, db: Session = Depends(get_orbit_db)):
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Not found")

    print(f"[UPDATE] 开始更新书架 {bookshelf_id}")
    print(f"[UPDATE] 输入 payload: {payload}")

    if payload.name:
        bs.name = payload.name
        print(f"[UPDATE] 更新 name: {payload.name}")
    if payload.description is not None:
        bs.description = payload.description
        print(f"[UPDATE] 更新 description: {payload.description}")
    if payload.cover_url is not None:
        bs.cover_url = payload.cover_url
        print(f"[UPDATE] 更新 cover_url: {payload.cover_url}")
    if payload.icon is not None:
        bs.icon = payload.icon
        print(f"[UPDATE] 更新 icon: {payload.icon}")
    if payload.priority is not None:
        bs.priority = payload.priority
        print(f"[UPDATE] 更新 priority: {payload.priority}")
    if payload.urgency is not None:
        bs.urgency = payload.urgency
        print(f"[UPDATE] 更新 urgency: {payload.urgency}")
    if payload.tags is not None:
        bs.tags = payload.tags
        print(f"[UPDATE] 更新 tags: {payload.tags}")
    if payload.color is not None:
        bs.color = payload.color
        print(f"[UPDATE] 更新 color: {payload.color}")
    if payload.is_favorite is not None:
        bs.is_favorite = payload.is_favorite
        print(f"[UPDATE] 更新 is_favorite: {payload.is_favorite}")

    bs.updated_at = datetime.utcnow()
    db.add(bs)
    db.commit()
    db.refresh(bs)

    print(f"[UPDATE] 书架更新完成，最终 cover_url: {bs.cover_url}")

    return {
        "id": bs.id,
        "name": bs.name,
        "description": bs.description,
        "cover_url": bs.cover_url,
        "icon": bs.icon,
        "priority": bs.priority,
        "urgency": bs.urgency,
        "usage_count": bs.usage_count,
        "note_count": bs.note_count,
        "status": bs.status,
        "tags": bs.tags,
        "color": bs.color,
        "is_favorite": bs.is_favorite,
        "created_at": bs.created_at.isoformat() if bs.created_at else None,
        "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
    }

@router.delete("/bookshelves/{bookshelf_id}", status_code=204)
def delete_bookshelf(bookshelf_id: str, cascade: str = Query("orphan"), db: Session = Depends(get_orbit_db)):
    """
    删除书架

    业界标准方案（固定存储路径）:
    - cascade=orphan: 笔记的 bookshelf_id 设为 NULL（DB only）
    - 笔记文件保留在固定位置 storage/notes/{note_id}/（不动）
    - 删除书架文件夹 storage/bookshelves/{bookshelf_id}/（包括封面图）
    """
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Not found")

    if cascade == "orphan":
        # 将书架内的笔记转为自由笔记（DB only，文件不动）
        stmt_update = select(OrbitNote).where(OrbitNote.bookshelf_id == bookshelf_id)
        notes = db.execute(stmt_update).scalars().all()
        for note in notes:
            note.bookshelf_id = None
            db.add(note)
        print(f"[BOOKSHELF] Orphaned {len(notes)} notes from bookshelf {bs.name}")
        db.commit()

    # 删除书架的文件夹（包括封面图）
    storage_mgr.delete_bookshelf_storage(bookshelf_id)

    # 删除数据库中的书架记录
    db.delete(bs)
    db.commit()
    print(f"[BOOKSHELF] Deleted bookshelf {bs.name} and its storage")

@router.post("/bookshelves/{bookshelf_id}/notes/{note_id}", response_model=dict)
def add_note_to_bookshelf(bookshelf_id: str, note_id: str, db: Session = Depends(get_orbit_db)):
    """
    将笔记添加到书架

    业界标准方案（固定存储路径）:
    - 仅更新 DB 中的 bookshelf_id（DB only）
    - 笔记文件保留在固定位置 storage/notes/{note_id}/（不动）
    """
    stmt_bs = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt_bs).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    stmt_note = select(OrbitNote).where(OrbitNote.id == note_id)
    note = db.execute(stmt_note).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # 如果笔记已在其他书架，先从旧书架移除
    if note.bookshelf_id and note.bookshelf_id != bookshelf_id:
        old_bs_stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == note.bookshelf_id)
        old_bs = db.execute(old_bs_stmt).scalars().first()
        if old_bs:
            old_bs.note_count = max(0, (old_bs.note_count or 0) - 1)
            print(f"[BOOKSHELF] Removed from {old_bs.name}, note_count -> {old_bs.note_count}")
            db.add(old_bs)

    # 更新笔记的书架 ID（DB only）
    note.bookshelf_id = bookshelf_id
    db.add(note)

    # 增加新书架的笔记计数
    bs.note_count = (bs.note_count or 0) + 1
    print(f"[BOOKSHELF] Added to {bs.name}, note_count -> {bs.note_count}")
    db.add(bs)
    db.commit()

    return {"success": True, "message": "Added", "note_id": str(note.id)}

@router.delete("/bookshelves/{bookshelf_id}/notes/{note_id}", status_code=204)
def remove_note_from_bookshelf(bookshelf_id: str, note_id: str, db: Session = Depends(get_orbit_db)):
    """
    从书架中移除笔记

    业界标准方案（固定存储路径）:
    - 仅更新 DB 中的 bookshelf_id 为 NULL（DB only）
    - 笔记文件保留在固定位置 storage/notes/{note_id}/（不动）
    """
    stmt_bs = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt_bs).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    stmt = select(OrbitNote).where(OrbitNote.id == note_id)
    note = db.execute(stmt).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # 更新笔记的书架 ID 为 NULL（DB only）
    note.bookshelf_id = None
    db.add(note)

    # 减少书架的笔记计数
    bs.note_count = max(0, (bs.note_count or 0) - 1)
    print(f"[BOOKSHELF] Removed from {bs.name}, note_count -> {bs.note_count}")
    db.add(bs)
    db.commit()

@router.get("/bookshelves/{bookshelf_id}/notes", response_model=List[NoteOut])
def get_bookshelf_notes(
    bookshelf_id: str,
    sort_by: str = Query("-updated_at"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_orbit_db)
):
    """
    获取书架内的笔记，返回完整卡片预览信息（包括图片、内容等）
    """
    from app.routers.orbit.notes import extract_first_image, extract_preview_text

    print(f"[DEBUG] GET /bookshelves/{bookshelf_id}/notes - querying for notes with bookshelf_id={bookshelf_id}")

    stmt_bs = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt_bs).scalars().first()
    if not bs:
        print(f"[DEBUG] Bookshelf {bookshelf_id} not found")
        raise HTTPException(status_code=404, detail="Not found")

    stmt = select(OrbitNote).options(joinedload(OrbitNote.tags_rel)).where(OrbitNote.bookshelf_id == bookshelf_id)
    if sort_by == "-updated_at":
        stmt = stmt.order_by(desc(OrbitNote.updated_at))
    elif sort_by == "-created_at":
        stmt = stmt.order_by(desc(OrbitNote.created_at))
    elif sort_by == "created_at":
        stmt = stmt.order_by(asc(OrbitNote.created_at))
    stmt = stmt.limit(limit).offset(offset)
    notes = db.execute(stmt).unique().scalars().all()  # ✅ unique() 必需，因为 joinedload collection

    print(f"[DEBUG] Found {len(notes)} notes in bookshelf {bookshelf_id}")

    # 构建 NoteOut 对象，添加 bookshelf_tag 和预览信息
    result = []
    bookshelf_tag = BookshelfTagInfo(
        id=str(bs.id),
        name=bs.name,
        color=bs.color or "#00BCD4",
        icon=bs.icon
    )

    for note in notes:
        # 构造 tags_rel 对象列表
        tags_rel_list = []
        if note.tags_rel:
            for tag in note.tags_rel:
                tags_rel_list.append({
                    'id': str(tag.id),
                    'name': tag.name,
                    'color': tag.color,
                    'icon': tag.icon,
                    'description': tag.description,
                    'count': tag.count or 0
                })

        # 调试日志
        print(f"[DEBUG] 处理笔记 {note.id}:")
        print(f"  title: {note.title}")
        print(f"  preview_image: {note.preview_image}")
        print(f"  blocks_json: {note.blocks_json[:50] if note.blocks_json else None}...")

        # 显式构造 NoteOut，确保所有字段都被正确赋值
        note_out = NoteOut(
            id=str(note.id),
            title=note.title,
            summary=note.summary,  # 添加 summary
            content_md=note.content_md or "",
            blocks_json=note.blocks_json,  # 添加 blocks_json
            storage_path=note.storage_path,
            status=note.status,
            priority=note.priority,
            urgency=note.urgency,
            usage_level=note.usage_level,
            usage_count=note.usage_count,  # 确保 usage_count 被赋值
            tags=note.tags or [],  # 确保 tags 被赋值
            tags_rel=tags_rel_list,  # 构造后的标签对象列表
            due_at=note.due_at,
            created_at=note.created_at,
            updated_at=note.updated_at,
            bookshelf_id=str(note.bookshelf_id) if note.bookshelf_id else None,
            bookshelf_tag=bookshelf_tag,  # 添加书架标签
            preview_image=note.preview_image,  # ✅ 使用数据库中的 preview_image
            preview_text=note.summary or extract_preview_text(note.content_md, max_length=100),  # 优先使用 summary
            is_pinned=note.is_pinned,
            pinned_at=note.pinned_at,
        )
        result.append(note_out)

    return result

@router.post("/notes/{note_id}/move-to-bookshelf", response_model=dict)
def move_note_to_bookshelf(note_id: str, payload: MoveNoteRequest, db: Session = Depends(get_orbit_db)):
    """
    将笔记移动到书架

    业界标准方案（固定存储路径）:
    - 仅更新 DB 中的 bookshelf_id（DB only）
    - 笔记文件保留在固定位置 storage/notes/{note_id}/（不动）
    """
    stmt_note = select(OrbitNote).where(OrbitNote.id == note_id)
    note = db.execute(stmt_note).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    stmt_bs = select(OrbitBookshelf).where(OrbitBookshelf.id == payload.target_bookshelf_id)
    bs = db.execute(stmt_bs).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    # 如果笔记已在其他书架，先从旧书架移除（DB only）
    old_bs = None
    if note.bookshelf_id and note.bookshelf_id != payload.target_bookshelf_id:
        old_bs_stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == note.bookshelf_id)
        old_bs = db.execute(old_bs_stmt).scalars().first()
        if old_bs:
            old_bs.note_count = max(0, (old_bs.note_count or 0) - 1)
            print(f"[BOOKSHELF] Removed from {old_bs.name}, note_count -> {old_bs.note_count}")
            db.add(old_bs)

    # 更新笔记的书架 ID（DB only）
    note.bookshelf_id = bs.id
    db.add(note)

    # 增加新书架的笔记计数
    bs.note_count = (bs.note_count or 0) + 1
    print(f"[BOOKSHELF] Moved to {bs.name}, note_count -> {bs.note_count}")
    db.add(bs)
    db.commit()

    return {"success": True, "message": "Moved", "note_id": str(note.id), "bookshelf_id": str(bs.id)}

@router.post("/bookshelves/{bookshelf_id}/increment-usage", response_model=BookshelfOut)
def increment_bookshelf_usage(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Not found")
    bs.usage_count = (bs.usage_count or 0) + 1
    bs.updated_at = datetime.utcnow()
    db.add(bs)
    db.commit()
    db.refresh(bs)
    return {
        "id": bs.id,
        "name": bs.name,
        "description": bs.description,
        "cover_url": bs.cover_url,
        "icon": bs.icon,
        "priority": bs.priority,
        "urgency": bs.urgency,
        "usage_count": bs.usage_count,
        "note_count": bs.note_count,
        "status": bs.status,
        "tags": bs.tags,
        "color": bs.color,
        "is_favorite": bs.is_favorite,
        "created_at": bs.created_at.isoformat() if bs.created_at else None,
        "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
    }

@router.post("/bookshelves/{bookshelf_id}/pin", response_model=BookshelfOut)
def pin_bookshelf(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    """置顶书架"""
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    bs.is_pinned = True
    bs.pinned_at = datetime.utcnow()
    bs.updated_at = datetime.utcnow()
    db.add(bs)
    db.commit()
    db.refresh(bs)

    return {
        "id": bs.id,
        "name": bs.name,
        "description": bs.description,
        "cover_url": bs.cover_url,
        "icon": bs.icon,
        "priority": bs.priority,
        "urgency": bs.urgency,
        "usage_count": bs.usage_count,
        "note_count": bs.note_count,
        "status": bs.status,
        "tags": bs.tags,
        "color": bs.color,
        "is_favorite": bs.is_favorite,
        "created_at": bs.created_at.isoformat() if bs.created_at else None,
        "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
    }

@router.post("/bookshelves/{bookshelf_id}/unpin", response_model=BookshelfOut)
def unpin_bookshelf(bookshelf_id: str, db: Session = Depends(get_orbit_db)):
    """取消置顶书架"""
    stmt = select(OrbitBookshelf).where(OrbitBookshelf.id == bookshelf_id)
    bs = db.execute(stmt).scalars().first()
    if not bs:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    bs.is_pinned = False
    bs.pinned_at = None
    bs.updated_at = datetime.utcnow()
    db.add(bs)
    db.commit()
    db.refresh(bs)

    return {
        "id": bs.id,
        "name": bs.name,
        "description": bs.description,
        "cover_url": bs.cover_url,
        "icon": bs.icon,
        "priority": bs.priority,
        "urgency": bs.urgency,
        "usage_count": bs.usage_count,
        "note_count": bs.note_count,
        "status": bs.status,
        "tags": bs.tags,
        "color": bs.color,
        "is_favorite": bs.is_favorite,
        "created_at": bs.created_at.isoformat() if bs.created_at else None,
        "updated_at": bs.updated_at.isoformat() if bs.updated_at else None,
    }