"""
Orbit Tags API Routes - 标签管理接口

包含：
- GET /orbit/tags - 获取所有标签（支持排序和搜索）
- POST /orbit/tags - 创建新标签
- PUT /orbit/tags/{tag_id} - 编辑标签（名称、颜色、描述）
- DELETE /orbit/tags/{tag_id} - 删除标签
"""

from __future__ import annotations
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, asc, func

from app.database_orbit import get_orbit_db
from app.models.orbit.tags import OrbitTag, OrbitNoteTag
from app.models.orbit.notes import OrbitNote

router = APIRouter(prefix="/orbit", tags=["Orbit-Tags"])

# ============================================================================
# Schemas
# ============================================================================

class TagOut(BaseModel):
    """标签输出模型"""
    id: str
    name: str
    color: str
    icon: Optional[str] = None
    description: Optional[str] = None
    count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, value: Optional[datetime], _info) -> Optional[str]:
        return value.isoformat() if value else None

    class Config:
        from_attributes = True


class TagIn(BaseModel):
    """标签输入模型"""
    name: str
    color: Optional[str] = "#808080"
    icon: Optional[str] = None
    description: Optional[str] = None


class TagUpdate(BaseModel):
    """标签更新模型"""
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/tags", response_model=List[TagOut])
def list_tags(
    sort: str = Query("frequency", regex="^(frequency|alphabetic|recent)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    search: Optional[str] = None,
    db: Session = Depends(get_orbit_db),
):
    """
    获取标签列表

    参数：
    - sort: 排序方式
      - frequency: 按使用频率从高到低
      - alphabetic: 按字母顺序
      - recent: 按最近创建时间
    - search: 搜索标签名称（支持模糊查询）
    - limit: 返回数量
    - offset: 分页偏移
    """
    stmt = select(OrbitTag)

    # 搜索过滤
    if search:
        stmt = stmt.where(OrbitTag.name.ilike(f"%{search}%"))

    # 排序
    if sort == "frequency":
        stmt = stmt.order_by(desc(OrbitTag.count))
    elif sort == "alphabetic":
        stmt = stmt.order_by(asc(OrbitTag.name))
    elif sort == "recent":
        stmt = stmt.order_by(desc(OrbitTag.created_at))

    # 分页
    stmt = stmt.limit(limit).offset(offset)

    tags = db.execute(stmt).scalars().all()
    return tags


@router.get("/tags/{tag_id}", response_model=TagOut)
def get_tag(tag_id: str, db: Session = Depends(get_orbit_db)):
    """获取单个标签详情"""
    tag = db.get(OrbitTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("/tags", response_model=TagOut)
def create_tag(payload: TagIn, db: Session = Depends(get_orbit_db)):
    """创建新标签"""
    # 检查标签是否已存在
    existing = db.execute(
        select(OrbitTag).where(OrbitTag.name == payload.name)
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail=f"Tag '{payload.name}' already exists")

    tag = OrbitTag(
        name=payload.name,
        color=payload.color or "#808080",
        icon=payload.icon,
        description=payload.description,
        count=0
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.put("/tags/{tag_id}", response_model=TagOut)
def update_tag(tag_id: str, payload: TagUpdate, db: Session = Depends(get_orbit_db)):
    """编辑标签"""
    tag = db.get(OrbitTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    # 如果修改名称，检查新名称是否已存在
    if payload.name and payload.name != tag.name:
        existing = db.execute(
            select(OrbitTag).where(OrbitTag.name == payload.name)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=409, detail=f"Tag '{payload.name}' already exists")
        tag.name = payload.name

    if payload.color:
        tag.color = payload.color
    if payload.icon is not None:
        tag.icon = payload.icon
    if payload.description is not None:  # 允许空描述
        tag.description = payload.description

    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}", status_code=204)
def delete_tag(tag_id: str, db: Session = Depends(get_orbit_db)):
    """
    删除标签

    此操作会：
    1. 删除标签
    2. 级联删除所有关联的 orbit_note_tags 记录
    3. 不会删除 Note 本身
    """
    tag = db.get(OrbitTag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()


@router.get("/tags/stats/summary")
def tag_stats_summary(db: Session = Depends(get_orbit_db)):
    """
    获取标签统计信息

    返回：
    - total_tags: 标签总数
    - total_usages: 总使用次数
    - top_5_tags: 使用最频繁的前 5 个标签
    """
    total_tags = db.query(func.count(OrbitTag.id)).scalar() or 0
    total_usages = db.query(func.sum(OrbitTag.count)).scalar() or 0

    top_5 = db.execute(
        select(OrbitTag).order_by(desc(OrbitTag.count)).limit(5)
    ).scalars().all()

    return {
        "total_tags": total_tags,
        "total_usages": total_usages,
        "top_5_tags": [{"name": t.name, "count": t.count, "color": t.color, "icon": t.icon} for t in top_5]
    }
