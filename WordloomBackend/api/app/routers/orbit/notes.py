from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, asc, desc, or_, case
from app.database_orbit import get_orbit_db, ORBIT_UPLOAD_DIR
# 改为正确路径
from app.models.orbit.notes import OrbitNote
from app.models.orbit.tags import OrbitTag, OrbitNoteTag
from app.core.image_manager import ImageManager

# 初始化图片管理器
image_manager = ImageManager(ORBIT_UPLOAD_DIR)

router = APIRouter(prefix="/orbit", tags=["Orbit-Notes"])

# ----- Schemas -----

class TagOutNested(BaseModel):
    """嵌套在 Note 中的标签对象"""
    id: str
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None
    count: int = 0

    class Config:
        from_attributes = True

class NoteOut(BaseModel):
    id: str
    title: Optional[str] = None
    content_md: Optional[str] = ""
    status: str = "open"
    priority: int = 3
    urgency: int = 3
    usage_level: int = 3
    usage_count: int = 0
    tags: List[str] = Field(default_factory=list)
    tags_rel: Optional[List[TagOutNested]] = Field(default_factory=list)  # 新增：标签对象
    due_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer('due_at', 'created_at', 'updated_at')
    def serialize_dt(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True

class NoteIn(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    urgency: Optional[int] = None
    usage_level: Optional[int] = None
    tags: Optional[List[str]] = None
    due_at: Optional[str] = None

class QuickCaptureIn(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    selection: Optional[str] = None
    tags: Optional[List[str]] = None

class DuplicateNoteRequest(BaseModel):
    """复制 Note 的请求体"""
    title_suffix: str = "(副本)"

    class Config:
        json_schema_extra = {
            "example": {
                "title_suffix": "(副本)"
            }
        }

# ----- Helpers -----
ALLOWED_SORT = {
    "created_at": lambda m: asc(m.created_at),
    "-created_at": lambda m: desc(m.created_at),
    "updated_at": lambda m: asc(m.updated_at),
    "-updated_at": lambda m: desc(m.updated_at),
    "due_at": lambda m: asc(m.due_at),
    "-due_at": lambda m: desc(m.due_at),
    "priority": lambda m: asc(m.priority),
    "-priority": lambda m: desc(m.priority),
    "urgency": lambda m: asc(m.urgency),
    "-urgency": lambda m: desc(m.urgency),
    "usage_level": lambda m: asc(m.usage_level),
    "-usage_level": lambda m: desc(m.usage_level),
    "usage_count": lambda m: asc(m.usage_count),
    "-usage_count": lambda m: desc(m.usage_count),
}

# ----- Endpoints -----
@router.get("/notes", response_model=list[NoteOut])
def list_notes(
    q: Optional[str] = None,
    tag: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "-updated_at",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_orbit_db),
):
    stmt = select(OrbitNote).options(joinedload(OrbitNote.tags_rel))

    # 搜索条件
    if q:
        like = f"%{q}%"
        search_condition = or_(OrbitNote.title.ilike(like), OrbitNote.content_md.ilike(like))
        stmt = stmt.where(search_condition)

        # 优先化排序：title 匹配的排在前面
        priority_case = case(
            (OrbitNote.title.ilike(like), 0),
            else_=1
        )
        order = ALLOWED_SORT.get(sort, ALLOWED_SORT["-updated_at"])
        stmt = stmt.order_by(priority_case, order(OrbitNote))
    else:
        order = ALLOWED_SORT.get(sort, ALLOWED_SORT["-updated_at"])
        stmt = stmt.order_by(order(OrbitNote))

    if tag:
        # 使用新的标签关系过滤：先找到标签ID，然后过滤
        tag_obj = db.query(OrbitTag).filter_by(name=tag).first()
        if tag_obj:
            stmt = stmt.join(OrbitNoteTag).where(OrbitNoteTag.tag_id == tag_obj.id)
    if status:
        stmt = stmt.where(OrbitNote.status == status)

    stmt = stmt.limit(limit).offset(offset)
    rows = db.execute(stmt).unique().scalars().all()
    return rows

@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: str, db: Session = Depends(get_orbit_db)):
    stmt = select(OrbitNote).where(OrbitNote.id == note_id).options(joinedload(OrbitNote.tags_rel))
    n = db.execute(stmt).unique().scalars().first()
    if not n:
        raise HTTPException(status_code=404, detail="note not found")
    return n

@router.post("/notes", response_model=NoteOut)
def create_note(payload: NoteIn, db: Session = Depends(get_orbit_db)):
    n = OrbitNote(
        title=payload.title,
        content_md=payload.content_md or "",
        status=payload.status or "open",
        priority=payload.priority or 3,
        urgency=payload.urgency or 3,
        usage_level=payload.usage_level or 3,
        tags=payload.tags or [],  # 保持旧字段向后兼容
        due_at=payload.due_at,
    )
    db.add(n)
    db.flush()  # 获取生成的 ID

    # 处理新的标签关系
    if payload.tags:
        for tag_name in payload.tags:
            # 查询或创建标签
            tag = db.query(OrbitTag).filter_by(name=tag_name).first()
            if not tag:
                tag = OrbitTag(name=tag_name)
                db.add(tag)
                db.flush()

            # 创建关联
            assoc = OrbitNoteTag(note_id=str(n.id), tag_id=tag.id)
            db.add(assoc)

    db.commit()
    db.refresh(n, ["tags_rel"])

    # 为新创建的 note 自动创建对应的图片文件夹
    image_manager.create_note_folder(str(n.id))

    return n

@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: str, payload: NoteIn, db: Session = Depends(get_orbit_db)):
    n = db.get(OrbitNote, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="note not found")

    for f in ("title", "content_md", "status", "priority", "urgency", "usage_level", "due_at"):
        v = getattr(payload, f, None)
        if v is not None:
            setattr(n, f, v)

    # 处理标签更新
    if payload.tags is not None:
        # 更新旧字段以保持向后兼容
        n.tags = payload.tags

        # 删除旧的标签关联
        db.query(OrbitNoteTag).filter_by(note_id=note_id).delete()

        # 创建新的标签关联
        for tag_name in payload.tags:
            tag = db.query(OrbitTag).filter_by(name=tag_name).first()
            if not tag:
                tag = OrbitTag(name=tag_name)
                db.add(tag)
                db.flush()

            assoc = OrbitNoteTag(note_id=note_id, tag_id=tag.id)
            db.add(assoc)

    db.add(n)
    db.commit()
    db.refresh(n, ["tags_rel"])

    # 更新内容后，清理未被引用的图片
    image_manager.cleanup_unused_images(note_id, n.content_md)

    return n

@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str, db: Session = Depends(get_orbit_db)):
    n = db.get(OrbitNote, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="note not found")

    # 删除标签关联
    db.query(OrbitNoteTag).filter_by(note_id=note_id).delete()

    db.delete(n)
    db.commit()

    # 删除 note 对应的整个图片文件夹
    image_manager.delete_note_folder(note_id)

@router.post("/notes/quick-capture", response_model=NoteOut)
def quick_capture(payload: QuickCaptureIn, db: Session = Depends(get_orbit_db)):
    title = payload.title
    parts: list[str] = []
    if payload.url:
        t = title or "link"
        parts.append(f"[{t}]({payload.url})")
        title = title or t
    if payload.selection:
        q = payload.selection.replace("\n", "\n> ")
        parts.append(f"> {q}")
        if not title:
            s = payload.selection.strip()
            title = s[:40] + ("..." if len(s) > 40 else "")
    if payload.content:
        parts.append(payload.content)
    n = OrbitNote(
        title=title,
        content_md="\n\n".join([p for p in parts if p]),
        tags=payload.tags or [],
        status="open",
        priority=3,
        urgency=3,
        usage_level=3,
    )
    db.add(n)
    db.flush()

    # 处理标签关系
    if payload.tags:
        for tag_name in payload.tags:
            tag = db.query(OrbitTag).filter_by(name=tag_name).first()
            if not tag:
                tag = OrbitTag(name=tag_name)
                db.add(tag)
                db.flush()

            assoc = OrbitNoteTag(note_id=str(n.id), tag_id=tag.id)
            db.add(assoc)

    db.commit()
    db.refresh(n, ["tags_rel"])
    return n

@router.post("/notes/{note_id}/increment-usage", response_model=NoteOut)
def increment_usage_count(note_id: str, db: Session = Depends(get_orbit_db)):
    """增加 note 的使用次数计数器"""
    n = db.get(OrbitNote, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="note not found")
    n.usage_count = (n.usage_count or 0) + 1
    db.add(n)
    db.commit()
    db.refresh(n)
    return n

@router.post("/notes/{note_id}/duplicate", response_model=NoteOut)
def duplicate_note(
    note_id: str,
    payload: DuplicateNoteRequest,
    db: Session = Depends(get_orbit_db),
):
    """
    复制一个 Note

    复制操作包括：
    - 创建新的 Note 记录（新 ID）
    - 复制所有标签关联
    - 复制上传的文件（图片、附件等）
    - 重置使用次数为 0

    Args:
        note_id: 原 Note 的 ID
        payload: 复制请求，包含新标题的后缀
        db: 数据库会话

    Returns:
        新创建的 Note 对象

    Raises:
        404: Note 不存在
        500: 文件复制失败或其他错误
    """
    from app.services.note_service import NoteService

    # 检查原 Note 是否存在
    original = db.get(OrbitNote, note_id)
    if not original:
        raise HTTPException(status_code=404, detail="note not found")

    try:
        note_service = NoteService(ORBIT_UPLOAD_DIR)
        new_note = note_service.duplicate_note(
            note_id,
            db,
            title_suffix=payload.title_suffix,
        )
        db.refresh(new_note, ["tags_rel"])
        return new_note
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to duplicate note: {str(e)}")