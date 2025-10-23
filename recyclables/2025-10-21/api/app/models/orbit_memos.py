# app/routers/orbit_memos.py  (fixed import path)
from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, desc, asc, or_

from app.database import get_db
from app.models_orbit import Memo, Task, TaskStatus, TaskPriority, TaskDomain

router = APIRouter(tags=["Orbit:Memos"])

class MemoBase(BaseModel):
    text: str = Field(..., min_length=1)
    tags: Optional[str] = None
    linked_source_id: Optional[int] = None
    linked_entry_id: Optional[int] = None

class MemoCreate(MemoBase): pass

class MemoUpdate(BaseModel):
    text: Optional[str] = None
    tags: Optional[str] = None
    linked_source_id: Optional[int] = None
    linked_entry_id: Optional[int] = None

class MemoOut(MemoBase):
    id: int
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

@router.get("/memos", response_model=List[MemoOut])
def list_memos(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    order: str = "desc",
    db: Session = Depends(get_db),
):
    stmt = select(Memo)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Memo.text.like(like), Memo.tags.like(like)))
    stmt = stmt.order_by(desc(Memo.created_at) if order != "asc" else asc(Memo.created_at))
    if page_size > 0:
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    return db.execute(stmt).scalars().all()

@router.post("/memos", response_model=MemoOut, status_code=201)
def create_memo(payload: MemoCreate, db: Session = Depends(get_db)):
    now = datetime.utcnow()
    memo = Memo(
        text=payload.text, tags=payload.tags,
        linked_source_id=payload.linked_source_id,
        linked_entry_id=payload.linked_entry_id,
        created_at=now, updated_at=now,
    )
    db.add(memo); db.commit(); db.refresh(memo)
    return memo

@router.patch("/memos/{memo_id}", response_model=MemoOut)
def update_memo(memo_id: int, payload: MemoUpdate, db: Session = Depends(get_db)):
    memo = db.get(Memo, memo_id)
    if not memo: raise HTTPException(404, "Memo not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(memo, k, v)
    memo.updated_at = datetime.utcnow()
    db.commit(); db.refresh(memo)
    return memo

@router.delete("/memos/{memo_id}", status_code=204)
def delete_memo(memo_id: int, db: Session = Depends(get_db)):
    memo = db.get(Memo, memo_id)
    if not memo: return
    db.delete(memo); db.commit()

class ConvertPayload(BaseModel):
    title: str = Field(..., min_length=1)
    note: Optional[str] = None
    priority: TaskPriority = TaskPriority.normal
    domain: TaskDomain = TaskDomain.dev
    due_at: Optional[datetime] = None

@router.post("/memos/{memo_id}/convert-to-task", response_model=dict)
def convert_to_task(memo_id: int, payload: ConvertPayload, db: Session = Depends(get_db)):
    memo = db.get(Memo, memo_id)
    if not memo: raise HTTPException(404, "Memo not found")
    task = Task(
        title=payload.title,
        note=payload.note or memo.text,
        status=TaskStatus.todo,
        priority=payload.priority,
        domain=payload.domain,
        source_id=memo.linked_source_id,
        entry_id=memo.linked_entry_id,
        due_at=payload.due_at,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(task); db.flush(); db.commit()
    return {"task_id": task.id}
