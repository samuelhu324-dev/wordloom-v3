"""Pydantic schemas for maturity module APIs."""
from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel


class ScoreComponentSchema(BaseModel):
    factor: str
    points: int
    detail: str


class MaturityScoreSchema(BaseModel):
    value: int
    components: List[ScoreComponentSchema]


class TransitionTaskSchema(BaseModel):
    code: str
    title: str
    description: str
    weight: int
    required_stage: str
    status: str


class MaturitySnapshotSchema(BaseModel):
    book_id: UUID
    stage: str
    score: MaturityScoreSchema
    tasks: List[TransitionTaskSchema]
    created_at: datetime
    manual_override: bool
    manual_reason: str | None = None
    blocks_count: int
    block_type_count: int
    todos_count: int
    tags_count: int
    visits_90d: int
    summary_length: int
    has_title: bool
    has_summary: bool
    has_cover_icon: bool
    operations_bonus: int
    last_visit_at: datetime | None = None
    last_event_at: datetime | None = None

    @classmethod
    def from_domain(cls, snapshot) -> "MaturitySnapshotSchema":  # pragma: no cover - DTO mapper
        stage_value = snapshot.stage.value if hasattr(snapshot.stage, "value") else str(snapshot.stage)
        score = MaturityScoreSchema(
            value=int(snapshot.score.value),
            components=[
                ScoreComponentSchema(
                    factor=str(component.factor),
                    points=int(component.points),
                    detail=str(component.detail),
                )
                for component in getattr(snapshot.score, "components", [])
            ],
        )
        tasks = [
            TransitionTaskSchema(
                code=str(task.code),
                title=str(task.title),
                description=str(task.description),
                weight=int(task.weight),
                required_stage=task.required_stage.value if hasattr(task, "required_stage") else "seed",
                status=task.status.value if hasattr(task, "status") else "pending",
            )
            for task in getattr(snapshot, "tasks", [])
        ]

        return cls(
            book_id=snapshot.book_id,
            stage=stage_value,
            score=score,
            tasks=tasks,
            created_at=snapshot.created_at,
            manual_override=bool(snapshot.manual_override),
            manual_reason=snapshot.manual_reason,
            blocks_count=getattr(snapshot, "blocks_count", 0),
            block_type_count=getattr(snapshot, "block_type_count", 0),
            todos_count=getattr(snapshot, "todos_count", 0),
            tags_count=getattr(snapshot, "tags_count", 0),
            visits_90d=getattr(snapshot, "visits_90d", 0),
            summary_length=getattr(snapshot, "summary_length", 0),
            has_title=bool(getattr(snapshot, "has_title", False)),
            has_summary=bool(getattr(snapshot, "has_summary", False)),
            has_cover_icon=bool(getattr(snapshot, "has_cover_icon", False)),
            operations_bonus=getattr(snapshot, "operations_bonus", 0),
            last_visit_at=getattr(snapshot, "last_visit_at", None),
            last_event_at=getattr(snapshot, "last_event_at", None),
        )
