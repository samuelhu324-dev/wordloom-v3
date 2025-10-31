# app/routers/orbit/tasks.py
# Orbit 模块 - 任务接口（保守兜底版）

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, or_
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models.orbit.tasks import Task, TaskEvent, TaskStatus, TaskPriority, TaskDomain

router = APIRouter(tags=["Orbit:Tasks"])  # 上层 main.py 已挂 prefix="/api/orbit" 的话，这里无需再写 prefix

# ---------- Pydantic 模型 ----------
class TaskBase(BaseModel):
    title: str = Field(..., max_length=300)
    note: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.normal
    domain: TaskDomain = TaskDomain.dev
    source_id: Optional[int] = None
    entry_id: Optional[int] = None
    due_at: Optional[datetime] = None

class TaskOut(TaskBase):
    id: int
    completed_at: Optional[datetime] = None
    # ⚠️ 为了兼容旧表结构，这里暂时设为 Optional
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ---------- 列表 ----------
@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    q: Optional[str] = None,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    domain: Optional[TaskDomain] = Query(None),
    db: Session = Depends(get_db),
):
    stmt = select(Task)

    # 模糊检索：Postgres 优先用 ilike；若驱动不支持则退回 like
    if q:
        like = f"%{q}%"
        if hasattr(Task.title, "ilike"):
            stmt = stmt.where(or_(Task.title.ilike(like), Task.note.ilike(like)))
        else:
            stmt = stmt.where(or_(Task.title.like(like), Task.note.like(like)))

    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if domain:
        stmt = stmt.where(Task.domain == domain)

    # ⚠️ 为避免“模型或表缺少 created_at 列”导致 500，这里先稳妥用 id 排序
    # 待 Alembic 同步后，你可以把这行改回 desc(Task.created_at)
    stmt = stmt.order_by(desc(Task.id))

    return db.execute(stmt).scalars().all()

# ---------- 新建 ----------
@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskBase, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    data = payload.model_dump()

    # 防御：如果有人传 None，则落默认值
    data.setdefault("status", TaskStatus.todo)
    data.setdefault("priority", TaskPriority.normal)
    data.setdefault("domain", TaskDomain.dev)

    task = Task(**data)

    # 仅当模型里有这些列时才赋值，避免 AttributeError
    if hasattr(Task, "created_at"):
        task.created_at = now
    if hasattr(Task, "updated_at"):
        task.updated_at = now

    db.add(task)
    db.flush()

    # 事件表可选：没有 TaskEvent 或表未迁移也不影响主流程
    try:
        db.add(TaskEvent(task_id=task.id, kind="created", ts=now))
    except Exception:
        pass

    db.commit()
    db.refresh(task)
    return task
