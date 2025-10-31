# app/models/orbit/tasks.py
# Orbit 模块 - Task 与 TaskEvent 模型定义

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SAEnum, Index
from sqlalchemy.orm import relationship
from app.models.core import Base

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
    entry_id = Column(Integer, ForeignKey("entries.id"), nullable=True)
    due_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("Source", lazy="joined", uselist=False)
    entry = relationship("Entry", lazy="joined", uselist=False)

    __table_args__ = (
        Index("ix_tasks_status", "status"),
        Index("ix_tasks_priority", "priority"),
        Index("ix_tasks_domain", "domain"),
        Index("ix_tasks_due_at", "due_at"),
    )

class TaskEvent(Base):
    __tablename__ = "task_events"
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(50), nullable=False)
    ts = Column(DateTime, default=datetime.utcnow, nullable=False)
