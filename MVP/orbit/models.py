from __future__ import annotations
from sqlalchemy import String, Integer, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from db import Base
import enum

class MemoStatus(str, enum.Enum):
    draft = "draft"
    done = "done"

class TaskStatus(str, enum.Enum):
    todo = "todo"
    doing = "doing"
    done = "done"

class Memo(Base):
    __tablename__ = "memos"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    text: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[str] = mapped_column(String(500), default="")   # 逗号分隔
    source: Mapped[str] = mapped_column(String(200), default="")
    links: Mapped[str] = mapped_column(String(1000), default="") # 逗号分隔
    status: Mapped[MemoStatus] = mapped_column(Enum(MemoStatus), default=MemoStatus.draft)

    tasks: Mapped[list["Task"]] = relationship(back_populates="memo", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.todo, index=True)
    effort: Mapped[int] = mapped_column(Integer, default=3)  # 1-5
    memo_id: Mapped[int | None] = mapped_column(ForeignKey("memos.id"), nullable=True)

    memo: Mapped["Memo | None"] = relationship(back_populates="tasks")
