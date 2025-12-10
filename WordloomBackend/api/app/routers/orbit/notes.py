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
from app.core.storage_manager import StorageManager

# 初始化图片管理器和存储管理器
image_manager = ImageManager(ORBIT_UPLOAD_DIR)
storage_mgr = StorageManager(ORBIT_UPLOAD_DIR)

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

class BookshelfTagInfo(BaseModel):
    """书架标签信息（用于笔记卡片显示）"""
    id: str
    name: str
    color: str = "#00BCD4"
    icon: Optional[str] = None

    class Config:
        from_attributes = True

class NoteOut(BaseModel):
    id: str
    title: Optional[str] = None
    summary: Optional[str] = None  # 新增：Note 摘要/描述
    content_md: Optional[str] = ""
    blocks_json: Optional[str] = None  # 新增：JSON格式的blocks数组
    storage_path: Optional[str] = None  # 业界标准：固定存储路径
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
    bookshelf_id: Optional[str] = None
    bookshelf_tag: Optional[BookshelfTagInfo] = None  # 新增：书架标签信息
    preview_image: Optional[str] = None  # 新增：首张图片用于预览
    preview_text: Optional[str] = None  # 新增：预览文本
    cover_image_url: Optional[str] = None  # 新增：封面图 URL
    cover_image_display_width: Optional[int] = None  # 新增：封面图显示宽度
    is_pinned: bool = False  # 新增：是否置顶
    pinned_at: Optional[datetime] = None  # 新增：置顶时间

    @field_serializer('due_at', 'created_at', 'updated_at', 'pinned_at')
    def serialize_dt(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True
        # 确保所有字段都被序列化，即使为 None
        populate_by_name = True

class NoteIn(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None  # 新增：Note 摘要/描述
    content_md: Optional[str] = None
    blocks_json: Optional[str] = None  # 新增：JSON格式的blocks数组
    status: Optional[str] = None
    priority: Optional[int] = None
    urgency: Optional[int] = None
    usage_level: Optional[int] = None
    tags: Optional[List[str]] = None
    due_at: Optional[str] = None
    bookshelf_id: Optional[str] = None  # 如果传递，则创建到书架内，否则创建到自由标签

class QuickCaptureIn(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    selection: Optional[str] = None
    tags: Optional[List[str]] = None
    bookshelf_id: Optional[str] = None  # 可选的书架ID

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

def extract_first_image(content_md: Optional[str]) -> Optional[str]:
    """从 markdown 内容中提取首张图片 URL（转换为前端兼容格式）"""
    if not content_md:
        return None

    import re
    # 匹配 markdown 图片格式: ![...](url)
    md_pattern = r'!\[.*?\]\(([^)]+)\)'
    match = re.search(md_pattern, content_md)
    if match:
        url = match.group(1)
        # 转换 URL 格式：若是 /uploads/xxx/yyy，保持不变；否则返回原 URL
        return normalize_image_url(url)

    # 匹配 HTML img 标签
    html_pattern = r'<img\s+(?:[^>]*?\s+)?src=["\']?([^"\'>\s]+)["\']?'
    match = re.search(html_pattern, content_md, re.IGNORECASE)
    if match:
        url = match.group(1)
        return normalize_image_url(url)

    return None

def normalize_image_url(url: str) -> str:
    """
    规范化图片 URL 格式

    新架构存储在: storage/orbit_uploads/notes/{note_id}/images/{filename}
    前端期望:     /uploads/{note_id}/{filename}

    所以无需转换，直接返回（因为前端上传时已经用的是 /uploads/{note_id}/{filename}）
    """
    return url

def extract_preview_text(content_md: Optional[str], max_length: int = 100) -> Optional[str]:
    """从 markdown 内容中提取预览文本（去除格式符号和 HTML 标签）"""
    if not content_md:
        return None

    import re
    # 移除 HTML 标签（如果有的话）
    text = re.sub(r'<[^>]*>', '', content_md)
    # 移除 markdown 图片、链接、代码等格式
    text = re.sub(r'!\[.*?\]\([^)]+\)', '', text)  # 移除图片
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # 移除链接但保留文本
    text = re.sub(r'```[\s\S]*?```', '', text)  # 移除代码块
    text = re.sub(r'`([^`]+)`', r'\1', text)  # 移除行内代码
    text = re.sub(r'[#*_~\-=]+', '', text)  # 移除 markdown 格式符
    text = text.strip()

    # 只取前 max_length 个字符
    if len(text) > max_length:
        return text[:max_length] + '...'
    return text if text else None

def extract_first_image_from_blocks(blocks_json: Optional[str]) -> Optional[str]:
    """从 blocks_json 中提取第一张图片 URL（用作 Note 预览图）

    业界标准：
    - 检查 blocks 数组中的第一个 'image' 类型的 block
    - 提取其 content.url
    - 返回 None 如果没有找到图片
    """
    if not blocks_json:
        return None

    try:
        import json
        blocks = json.loads(blocks_json)
        for block in blocks:
            if block.get('type') == 'image':
                url = block.get('content', {}).get('url')
                if url:
                    print(f"[EXTRACT_IMAGE] 从 blocks 中提取到第一张图片: {url}")
                    return url
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[EXTRACT_IMAGE] 解析 blocks_json 失败: {e}")

    return None

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
    has_bookshelf: Optional[bool] = None,
    db: Session = Depends(get_orbit_db),
):
    """
    获取笔记列表

    参数：
    - has_bookshelf: None (不过滤), True (只有书架笔记), False (只有自由笔记)
    """
    stmt = select(OrbitNote).options(joinedload(OrbitNote.tags_rel))  # ✅ 加载标签关系

    # ✅ bookshelf 过滤
    if has_bookshelf is None:
        # 默认只显示自由笔记（向后兼容）
        stmt = stmt.where(OrbitNote.bookshelf_id == None)
    elif has_bookshelf is True:
        # 只显示有书架的笔记
        stmt = stmt.where(OrbitNote.bookshelf_id != None)
    else:
        # 只显示自由笔记
        stmt = stmt.where(OrbitNote.bookshelf_id == None)

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

    # 将 ORM 对象转换为 NoteOut，添加预览字段
    result = []
    for row in rows:
        # 构造 tags_rel 对象列表
        tags_rel_list = []
        if row.tags_rel:
            for tag in row.tags_rel:
                tags_rel_list.append({
                    'id': str(tag.id),
                    'name': tag.name,
                    'color': tag.color,
                    'icon': tag.icon,
                    'description': tag.description,
                    'count': tag.count or 0
                })

        # 显式构造 NoteOut，确保所有字段都被正确赋值
        note_out = NoteOut(
            id=str(row.id),
            title=row.title,
            summary=row.summary,  # 新增：返回 summary 字段
            content_md=row.content_md or "",
            blocks_json=row.blocks_json,  # ✅ 也返回 blocks_json，用于前端使用
            storage_path=row.storage_path,
            status=row.status,
            priority=row.priority,
            urgency=row.urgency,
            usage_level=row.usage_level,
            usage_count=row.usage_count,  # 确保 usage_count 被赋值
            tags=row.tags or [],  # 确保 tags 被赋值
            tags_rel=tags_rel_list,  # 构造后的标签对象列表
            due_at=row.due_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
            bookshelf_id=str(row.bookshelf_id) if row.bookshelf_id else None,
            bookshelf_tag=None,  # 自由笔记没有 shelf 标签
            preview_image=row.preview_image or extract_first_image_from_blocks(row.blocks_json),  # ✅ 优先使用 preview_image，降级从 blocks_json 提取
            preview_text=row.summary or extract_preview_text(row.content_md),  # 优先使用 summary
            is_pinned=row.is_pinned,
            pinned_at=row.pinned_at,
        )
        result.append(note_out)

    return result

@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: str, db: Session = Depends(get_orbit_db)):
    stmt = select(OrbitNote).where(OrbitNote.id == note_id).options(joinedload(OrbitNote.tags_rel))
    n = db.execute(stmt).unique().scalars().first()
    if not n:
        raise HTTPException(status_code=404, detail="note not found")

    # 确保 ORM 对象完全加载所有字段
    print(f"\n[GET_NOTE] 返回 note {note_id}:")
    print(f"  title = {n.title}")
    print(f"  blocks_json 长度 = {len(n.blocks_json or '')}")

    # 手动序列化检查

    return n

@router.post("/notes", response_model=NoteOut)
def create_note(payload: NoteIn, db: Session = Depends(get_orbit_db)):
    """
    创建新笔记

    业界标准方案（固定存储路径）:
    - storage_path 在创建时生成，永不改变
    - bookshelf_id 只是业务关系，不影响存储位置
    """
    import uuid

    # 先生成 ID 和 storage_path
    note_id = str(uuid.uuid4())
    storage_path = f"notes/{note_id}"

    print(f"[DEBUG] POST /notes: title={payload.title}, bookshelf_id={payload.bookshelf_id}")

    n = OrbitNote(
        id=note_id,  # 显式设置 ID
        title=payload.title,
        summary=payload.summary,  # 新增：Note 摘要/描述
        content_md=payload.content_md or "",
        blocks_json=payload.blocks_json,  # 新增：JSON格式的blocks
        status=payload.status or "open",
        priority=payload.priority or 3,
        urgency=payload.urgency or 3,
        usage_level=payload.usage_level or 3,
        tags=payload.tags or [],
        due_at=payload.due_at,
        bookshelf_id=payload.bookshelf_id,
        storage_path=storage_path,  # 必须在创建时设置！
    )
    db.add(n)
    db.flush()

    # 创建存储目录
    try:
        storage_mgr.create_note_storage(note_id)
        print(f"[STORAGE] Created note {note_id} -> storage_path={storage_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create storage for {note_id}: {e}")
        db.rollback()
        raise

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

    # 如果创建时指定了书架，增加书架的笔记计数
    if payload.bookshelf_id:
        from app.models.orbit.bookshelves import OrbitBookshelf
        bookshelf = db.query(OrbitBookshelf).filter_by(id=payload.bookshelf_id).first()
        if bookshelf:
            bookshelf.note_count = (bookshelf.note_count or 0) + 1
            print(f"[BOOKSHELF] Incremented note_count for {bookshelf.name} -> {bookshelf.note_count}")
            db.add(bookshelf)

    db.commit()
    db.refresh(n, ["tags_rel"])

    return n

@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: str, payload: NoteIn, db: Session = Depends(get_orbit_db)):
    n = db.get(OrbitNote, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="note not found")

    # 添加详细日志，特别是 blocks_json
    print(f"\n[PUT_NOTE] 收到更新请求:")
    print(f"  note_id = {note_id}")
    print(f"  payload.blocks_json = {payload.blocks_json[:100] if payload.blocks_json else None}...")

    for f in ("title", "summary", "content_md", "blocks_json", "status", "priority", "urgency", "usage_level", "due_at"):
        v = getattr(payload, f, None)
        if v is not None:
            print(f"[PUT_NOTE]   设置 {f} = {str(v)[:50] if isinstance(v, str) else v}...")
            setattr(n, f, v)

    # ✅ 新增：如果收到了 blocks_json，自动提取第一张图片作为预览图
    if payload.blocks_json:
        preview_url = extract_first_image_from_blocks(payload.blocks_json)
        if preview_url:
            n.preview_image = preview_url  # 自动设置预览图
            print(f"[PUT_NOTE]   自动提取预览图 = {preview_url}")
        else:
            print(f"[PUT_NOTE]   ⚠️ blocks_json 中没有找到图片，preview_image 保持不变")

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

    # 更新内容后，清理未被引用的图片（同时检查 content_md 和 blocks_json）
    image_manager.cleanup_unused_images(note_id, n.content_md, n.blocks_json)

    return n

@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: str, db: Session = Depends(get_orbit_db)):
    """
    删除笔记

    业界标准方案（固定存储路径）:
    - 从 DB 中删除笔记记录
    - 若有 bookshelf_id，减少书架笔记计数
    - 删除固定存储位置的所有文件（storage/notes/{note_id}/）
    """
    n = db.get(OrbitNote, note_id)
    if not n:
        raise HTTPException(status_code=404, detail="note not found")

    # 删除标签关联
    db.query(OrbitNoteTag).filter_by(note_id=note_id).delete()

    # 如果笔记在书架内，减少书架的笔记计数
    if n.bookshelf_id:
        from app.models.orbit.bookshelves import OrbitBookshelf
        bookshelf = db.query(OrbitBookshelf).filter_by(id=n.bookshelf_id).first()
        if bookshelf:
            bookshelf.note_count = max(0, (bookshelf.note_count or 0) - 1)
            print(f"[BOOKSHELF] Decremented note_count for {bookshelf.name} -> {bookshelf.note_count}")
            db.add(bookshelf)

    # 删除数据库记录
    db.delete(n)
    db.commit()

    # 删除固定存储位置的所有文件（一次操作，无条件）
    try:
        storage_mgr.delete_note_storage(note_id)
        print(f"[STORAGE] Deleted note storage: notes/{note_id}")
    except Exception as e:
        print(f"[ERROR] Failed to delete note storage {note_id}: {e}")

@router.post("/notes/quick-capture", response_model=NoteOut)
def quick_capture(payload: QuickCaptureIn, db: Session = Depends(get_orbit_db)):
    """快速捕获笔记，支持 bookshelf_id"""
    import uuid

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

    # 生成 ID 和 storage_path
    note_id = str(uuid.uuid4())
    storage_path = f"notes/{note_id}"

    n = OrbitNote(
        id=note_id,  # 显式设置 ID
        title=title,
        content_md="\n\n".join([p for p in parts if p]),
        tags=payload.tags or [],
        status="open",
        priority=3,
        urgency=3,
        usage_level=3,
        bookshelf_id=payload.bookshelf_id,
        storage_path=storage_path,  # 必须在创建时设置！
    )
    db.add(n)
    db.flush()

    # 创建存储目录
    try:
        storage_mgr.create_note_storage(note_id)
        print(f"[STORAGE] Created quick capture note {note_id} -> storage_path={storage_path}")
    except Exception as e:
        print(f"[ERROR] Failed to create storage for {note_id}: {e}")
        db.rollback()
        raise

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

    # 如果指定了书架，增加书架笔记计数
    if payload.bookshelf_id:
        from app.models.orbit.bookshelves import OrbitBookshelf
        bookshelf = db.query(OrbitBookshelf).filter_by(id=payload.bookshelf_id).first()
        if bookshelf:
            bookshelf.note_count = (bookshelf.note_count or 0) + 1
            print(f"[BOOKSHELF] Incremented note_count for {bookshelf.name} -> {bookshelf.note_count}")
            db.add(bookshelf)

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

@router.post("/notes/{note_id}/pin", response_model=NoteOut)
def pin_note(note_id: str, db: Session = Depends(get_orbit_db)):
    """置顶 Note"""
    stmt = select(OrbitNote).where(OrbitNote.id == note_id)
    note = db.execute(stmt).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.is_pinned = True
    note.pinned_at = datetime.utcnow()
    note.updated_at = datetime.utcnow()
    db.add(note)
    db.commit()
    db.refresh(note, ["tags_rel", "bookshelf"])

    # 构造响应（参考 list_notes 的做法）
    bookshelf_tag = None
    if note.bookshelf:
        bookshelf_tag = {
            'id': str(note.bookshelf.id),
            'name': note.bookshelf.name,
            'color': note.bookshelf.color or "#00BCD4",
            'icon': note.bookshelf.icon,
        }

    return NoteOut(
        id=str(note.id),
        title=note.title,
        summary=note.summary,  # 新增：包含 summary
        content_md=note.content_md or "",
        storage_path=note.storage_path,
        status=note.status,
        priority=note.priority,
        urgency=note.urgency,
        usage_level=note.usage_level,
        usage_count=note.usage_count,
        tags=note.tags or [],
        due_at=note.due_at,
        created_at=note.created_at,
        updated_at=note.updated_at,
        bookshelf_id=str(note.bookshelf_id) if note.bookshelf_id else None,
        bookshelf_tag=bookshelf_tag,
        is_pinned=note.is_pinned,
        pinned_at=note.pinned_at,
    )

@router.post("/notes/{note_id}/unpin", response_model=NoteOut)
def unpin_note(note_id: str, db: Session = Depends(get_orbit_db)):
    """取消置顶 Note"""
    stmt = select(OrbitNote).where(OrbitNote.id == note_id)
    note = db.execute(stmt).scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.is_pinned = False
    note.pinned_at = None
    note.updated_at = datetime.utcnow()
    db.add(note)
    db.commit()
    db.refresh(note, ["tags_rel", "bookshelf"])

    # 构造响应
    bookshelf_tag = None
    if note.bookshelf:
        bookshelf_tag = {
            'id': str(note.bookshelf.id),
            'name': note.bookshelf.name,
            'color': note.bookshelf.color or "#00BCD4",
            'icon': note.bookshelf.icon,
        }

    return NoteOut(
        id=str(note.id),
        title=note.title,
        summary=note.summary,  # 新增：包含 summary
        content_md=note.content_md or "",
        storage_path=note.storage_path,
        status=note.status,
        priority=note.priority,
        urgency=note.urgency,
        usage_level=note.usage_level,
        usage_count=note.usage_count,
        tags=note.tags or [],
        due_at=note.due_at,
        created_at=note.created_at,
        updated_at=note.updated_at,
        bookshelf_id=str(note.bookshelf_id) if note.bookshelf_id else None,
        bookshelf_tag=bookshelf_tag,
        is_pinned=note.is_pinned,
        pinned_at=note.pinned_at,
    )