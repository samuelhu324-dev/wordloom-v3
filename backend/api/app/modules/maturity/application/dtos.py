"""Application-level DTOs for maturity workflows."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID

from ..domain import MaturitySignals, MaturitySnapshot, TransitionTask


@dataclass
class CalculateBookMaturityCommand:
    book_id: UUID
    persist_snapshot: bool = True
    tag_count: Optional[int] = None
    block_type_count: Optional[int] = None
    block_count: Optional[int] = None
    open_todo_count: Optional[int] = None
    operations_bonus: Optional[int] = None
    cover_icon: Optional[str] = None


@dataclass
class MaturitySnapshotResponse:
    snapshot: MaturitySnapshot


@dataclass
class GetSnapshotsQuery:
    book_id: UUID
    limit: int = 10


@dataclass
class MaturitySnapshotList:
    book_id: UUID
    snapshots: List[MaturitySnapshot]


@dataclass
class SnapshotPersistenceResult:
    snapshot: MaturitySnapshot
    persisted: bool


@dataclass
class SnapshotSignals:
    snapshot: MaturitySnapshot
    signals: MaturitySignals
    tasks: List[TransitionTask]
    manual_override: bool
    manual_reason: Optional[str]
