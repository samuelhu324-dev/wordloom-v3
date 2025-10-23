# app/routers/orbit_tasks.py
from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, asc, or_

from app.database import get_db
from app.models.orbit import Task, TaskEvent, TaskStatus, TaskPriority, TaskDomain

router = APIRouter(tags=["Orbit:Tasks"])

# —— Schemas —— #
class TaskBase(BaseModel):
    title: str = Field(..., max_length=300)
    note: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.normal
    domain: TaskDomain = TaskDomain.dev
    source_id: Optional[int] = None
    entry_id: Optional[int] = None
    due_at: Optional[datetime] = None

class TaskCreate(TaskBase): pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    note: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    domain: Optional[TaskDomain] = None
    source_id: Optional[int] = None
    entry_id: Optional[int] = None
    due_at: Optional[datetime] = None

class TaskOut(TaskBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

# —— Helpers —— #
def apply_filters(stmt, q, status, priority, domain, source_id, entry_id):
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Task.title.like(like), Task.note.like(like)))
    if status:   stmt = stmt.where(Task.status   == status)
    if priority: stmt = stmt.where(Task.priority == priority)
    if domain:   stmt = stmt.where(Task.domain   == domain)
    if source_id:stmt = stmt.where(Task.source_id== source_id)
    if entry_id: stmt = stmt.where(Task.entry_id == entry_id)
    return stmt

ORDER_FIELDS = {
    "created_at": Task.created_at,
    "updated_at": Task.updated_at,
    "due_at": Task.due_at,
    "priority": Task.priority,
    "id": Task.id,
}

# —— Routes —— #
@router.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    q: Optional[str] = None,
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    domain: Optional[TaskDomain] = Query(None),
    source_id: Optional[int] = Query(None),
    entry_id: Optional[int] = Query(None),
    page: int = 1,
    page_size: int = 50,
    order_by: Literal["created_at","updated_at","due_at","priority","id"] = "created_at",
    order: Literal["asc","desc"] = "desc",
    db: Session = Depends(get_db),
):
    stmt = select(Task)
    stmt = apply_filters(stmt, q, status, priority, domain, source_id, entry_id)
    col  = ORDER_FIELDS.get(order_by, Task.created_at)
    stmt = stmt.order_by(asc(col) if order == "asc" else desc(col))
    if page_size > 0:
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    return db.execute(stmt).scalars().all()

@router.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    task = Task(**payload.model_dump(), created_at=now, updated_at=now)
    db.add(task); db.flush()
    db.add(TaskEvent(task_id=task.id, kind="created", ts=now))
    db.commit(); db.refresh(task)
    return task

@router.patch("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task: raise HTTPException(404, "Task not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    if task.status == TaskStatus.done and task.completed_at is None:
        task.completed_at = datetime.utcnow()
        db.add(TaskEvent(task_id=task.id, kind="completed", ts=task.completed_at))
    task.updated_at = datetime.utcnow()
    db.commit(); db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task: return
    db.delete(task); db.commit()

class CompletePayload(BaseModel):
    when: Optional[datetime] = None

@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: int, payload: CompletePayload | None = None, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task: raise HTTPException(404, "Task not found")
    if task.status != TaskStatus.done: task.status = TaskStatus.done
    when = payload.when if payload and payload.when else datetime.utcnow()
    task.completed_at = when; task.updated_at = when
    db.add(TaskEvent(task_id=task.id, kind="completed", ts=when))
    db.commit(); db.refresh(task)
    return task

class SnoozePayload(BaseModel):
    days: int = Field(1, ge=1, le=365)

@router.post("/tasks/{task_id}/snooze", response_model=TaskOut)
def snooze_task(task_id: int, payload: SnoozePayload, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task: raise HTTPException(404, "Task not found")
    base = task.due_at or datetime.utcnow()
    task.due_at = base + timedelta(days=payload.days)
    task.updated_at = datetime.utcnow()
    db.add(TaskEvent(task_id=task.id, kind="snoozed", ts=datetime.utcnow()))
    db.commit(); db.refresh(task)
    return task
