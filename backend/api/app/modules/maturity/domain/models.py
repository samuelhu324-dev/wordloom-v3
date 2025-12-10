"""Domain models for the standalone maturity module."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:  # 避免运行时引入 Book 模块造成循环依赖
    from api.app.modules.book.domain import Book


class MaturityStage(str, Enum):
    """Semantic maturity stages for any knowledge unit."""

    SEED = "seed"
    GROWING = "growing"
    STABLE = "stable"
    LEGACY = "legacy"


@dataclass(frozen=True)
class ScoreComponent:
    """Granular scoring detail for UI explanations."""

    factor: str
    points: int
    detail: str


@dataclass(frozen=True)
class MaturityScore:
    """Aggregated score plus contributing components."""

    value: int
    components: List[ScoreComponent] = field(default_factory=list)


class StructureTaskStatus(str, Enum):
    """Lifecycle state for each structure task."""

    LOCKED = "locked"
    PENDING = "pending"
    COMPLETED = "completed"
    REGRESSED = "regressed"


@dataclass(frozen=True)
class StructureTask:
    """Blueprint for a structure task defined in Plan111."""

    code: str
    title: str
    description: str
    weight: int = 1
    required_stage: MaturityStage = MaturityStage.SEED


@dataclass(frozen=True)
class StructureTaskState(StructureTask):
    """Runtime state for a structure task bound to a snapshot."""

    status: StructureTaskStatus = StructureTaskStatus.PENDING


@dataclass(frozen=True)
class BookProfileSnapshot:
    """Minimal readonly data we need from the book aggregate."""

    book_id: UUID
    library_id: UUID
    bookshelf_id: UUID
    title: Optional[str]
    summary: Optional[str]
    cover_icon: Optional[str]
    maturity: Optional[MaturityStage]
    maturity_score: int = 0
    tag_count_snapshot: int = 0
    block_type_count: int = 0
    block_count: int = 0
    open_todo_snapshot: int = 0
    operations_bonus: int = 0
    visit_count_90d: int = 0
    last_visit_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None
    book: Optional["Book"] = None


@dataclass(frozen=True)
class MaturitySignals:
    """Facts derived from the provider used to recommend next tasks."""

    has_title: bool
    has_summary: bool
    has_tags: bool
    has_cover: bool
    block_count: int
    block_type_count: int
    open_todos: int


@dataclass(frozen=True)
class MaturitySnapshot:
    """Complete snapshot returned to clients (and optionally persisted)."""

    book_id: UUID
    stage: MaturityStage
    score: MaturityScore
    tasks: List[StructureTaskState]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    manual_override: bool = False
    manual_reason: Optional[str] = None
    blocks_count: int = 0
    block_type_count: int = 0
    todos_count: int = 0
    tags_count: int = 0
    visits_90d: int = 0
    summary_length: int = 0
    has_title: bool = False
    has_summary: bool = False
    has_cover_icon: bool = False
    operations_bonus: int = 0
    last_visit_at: Optional[datetime] = None
    last_event_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        def _serialize_task(task: StructureTaskState) -> dict:
            return {
                "code": task.code,
                "title": task.title,
                "description": task.description,
                "weight": task.weight,
                "required_stage": task.required_stage.value,
                "status": task.status.value,
            }

        return {
            "book_id": str(self.book_id),
            "stage": self.stage.value,
            "score": {
                "value": self.score.value,
                "components": [component.__dict__ for component in self.score.components],
            },
            "tasks": [_serialize_task(task) for task in self.tasks],
            "created_at": self.created_at.isoformat(),
            "manual_override": self.manual_override,
            "manual_reason": self.manual_reason,
            "blocks_count": self.blocks_count,
            "block_type_count": self.block_type_count,
            "todos_count": self.todos_count,
            "tags_count": self.tags_count,
            "visits_90d": self.visits_90d,
            "summary_length": self.summary_length,
            "has_title": self.has_title,
            "has_summary": self.has_summary,
            "has_cover_icon": self.has_cover_icon,
            "operations_bonus": self.operations_bonus,
            "last_visit_at": self.last_visit_at.isoformat() if self.last_visit_at else None,
            "last_event_at": self.last_event_at.isoformat() if self.last_event_at else None,
        }


# Backward compatibility alias for legacy imports
TransitionTask = StructureTaskState
