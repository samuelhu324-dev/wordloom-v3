# app/models_orbit.py
# NOTE: 放在 app/ 根下，避免 'app.models' 不是包导致的子模块导入错误。
from __future__ import annotations
from datetime import datetime
from enum import Enum
from sqlalchemy import (
    Column, Integer, String, DateTime, Enum as SAEnum, ForeignKey, Index, Text
)
from sqlalchemy.orm import relationship
from app.models import Base  # 复用现有 Base

class TaskStatus(str, Enum):
    todo = "todo"
    doing = "doing"
    done = "done"
    archived = "archived"

class TaskPriority(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"

class TaskDomain(str, Enum):
    dev = "dev"
    translate = "translate"
    research = "research"
    study = "study"

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    note = Column(Text, nullable=True)
    status = Column(SAEnum(TaskStatus, name="task_status", native_enum=False), nullable=False, default=TaskStatus.todo)
    priority = Column(SAEnum(TaskPriority, name="task_priority", native_enum=False), nullable=False, default=TaskPriority.normal)
    domain = Column(SAEnum(TaskDomain, name="task_domain", native_enum=False), nullable=False, default=TaskDomain.dev)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    entry_id  = Column(Integer, ForeignKey("entries.id"), nullable=True)
    due_at       = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    source = relationship("Source", lazy="joined", uselist=False)  # type: ignore
    entry  = relationship("Entry",  lazy="joined", uselist=False)  # type: ignore
    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_domain", "domain"),
        Index("ix_tasks_due_at", "due_at"),
        Index("ix_tasks_completed_at", "completed_at"),
        Index("ix_tasks_source_entry", "source_id", "entry_id"),
    )

class Memo(Base):
    __tablename__ = "memos"
    id   = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    tags = Column(String(300), nullable=True)
    linked_source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    linked_entry_id  = Column(Integer, ForeignKey("entries.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    linked_source = relationship("Source", lazy="joined", uselist=False)  # type: ignore
    linked_entry  = relationship("Entry",  lazy="joined", uselist=False)  # type: ignore
    __table_args__ = (Index("ix_memos_created_at", "created_at"),)

class TaskEvent(Base):
    __tablename__ = "task_events"
    id     = Column(Integer, primary_key=True, index=True)
    task_id= Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    kind   = Column(String(50), nullable=False)  # created / completed / reopened / snoozed
    ts     = Column(DateTime, default=datetime.utcnow, nullable=False)
