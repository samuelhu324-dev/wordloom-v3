from __future__ import annotations
from typing import Iterable, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from db import session_scope
from models import Memo, Task, MemoStatus, TaskStatus

# --------- Memo ---------
def create_memo(text:str, ts:datetime|None=None, tags:str="", source:str="", links:str="", status:MemoStatus=MemoStatus.draft) -> Memo:
    with session_scope() as s:
        m = Memo(text=text, ts=ts or datetime.utcnow(), tags=tags, source=source, links=links, status=status)
        s.add(m); s.flush()
        s.refresh(m)
        return m

def update_memo(mid:int, **fields) -> Memo | None:
    with session_scope() as s:
        m = s.get(Memo, mid)
        if not m: return None
        for k,v in fields.items():
            if hasattr(m,k) and v is not None: setattr(m,k,v)
        s.add(m)
        s.flush(); s.refresh(m)
        return m

def list_memos(q:str="", tag:str="", status:str="") -> list[Memo]:
    with session_scope() as s:
        stmt = select(Memo).order_by(Memo.ts.desc())
        if q: stmt = stmt.where(Memo.text.ilike(f"%{q}%"))
        if tag: stmt = stmt.where(Memo.tags.ilike(f"%{tag}%"))
        if status: stmt = stmt.where(Memo.status == status)
        return list(s.scalars(stmt).all())

# --------- Task ---------
def create_task(title:str, due_at:datetime|None=None, status:TaskStatus=TaskStatus.todo, effort:int=3, memo_id:int|None=None) -> Task:
    with session_scope() as s:
        t = Task(title=title, due_at=due_at, status=status, effort=effort, memo_id=memo_id)
        s.add(t); s.flush(); s.refresh(t)
        return t

def update_task(tid:int, **fields) -> Task | None:
    with session_scope() as s:
        t = s.get(Task, tid)
        if not t: return None
        for k,v in fields.items():
            if hasattr(t,k) and v is not None: setattr(t,k,v)
        s.add(t); s.flush(); s.refresh(t)
        return t

def transition_task(tid:int, to_status:TaskStatus) -> Task | None:
    return update_task(tid, status=to_status)

def list_tasks(status:str="", q:str="") -> list[Task]:
    with session_scope() as s:
        stmt = select(Task).order_by(Task.created_at.desc())
        if status: stmt = stmt.where(Task.status == status)
        if q: stmt = stmt.where(Task.title.ilike(f"%{q}%"))
        return list(s.scalars(stmt).all())

# --------- Stats ---------
def get_stats(days:int=7):
    cutoff = datetime.utcnow() - timedelta(days=days)
    with session_scope() as s:
        memos_count = s.scalar(select(func.count()).select_from(Memo).where(Memo.ts >= cutoff)) or 0
        tasks_done_count = s.scalar(select(func.count()).select_from(Task).where(Task.status == TaskStatus.done, Task.created_at >= cutoff)) or 0
        avg_effort = s.scalar(select(func.avg(Task.effort)).where(Task.created_at >= cutoff)) or 0
        return {
            "range_days": days,
            "memos_count": int(memos_count),
            "tasks_done_count": int(tasks_done_count),
            "avg_effort": float(avg_effort) if avg_effort else 0.0,
        }
