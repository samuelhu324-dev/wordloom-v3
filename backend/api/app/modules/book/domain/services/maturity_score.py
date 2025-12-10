"""Book maturity scoring service (Plan111 implementation).

This service keeps the calculation rules close to the domain while
remaining pure/side-effect free so it can be reused by application
use cases, scripts, or tests.  It follows the rule set captured in
Plan111 and DDD_RULES maturity policies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, List, Optional

from ..book import Book
from .plan111 import Plan111SnapshotInput, Plan111ScoreComponent, calculate_plan111_score


@dataclass(frozen=True)
class ScoreComponent:
    """Represents how many points a factor contributed to the final score."""

    factor: str
    points: int
    detail: str


@dataclass(frozen=True)
class BookMaturityScoreInput:
    """All data required to evaluate a Book's maturity score."""

    book: Book
    tag_count: int = 0
    block_type_count: int = 0
    block_count: int = 0
    open_todo_count: int = 0
    lucide_cover_icon: Optional[str] = None
    operations_bonus: int = 0  # Reserved 0-60 points for ops/manual adjustments
    visit_count_90d: int = 0
    last_content_edit_at: Optional[datetime] = None

    @property
    def has_title(self) -> bool:
        title = getattr(self.book, "title", None)
        if title is None:
            return False
        value = getattr(title, "value", title)
        return bool(value and str(value).strip())

    @property
    def has_summary(self) -> bool:
        summary = getattr(self.book, "summary", None)
        if summary is None:
            return False
        value = getattr(summary, "value", summary)
        return bool(value and str(value).strip())

    @property
    def cover_icon_selected(self) -> bool:
        icon = self.lucide_cover_icon
        if icon is None:
            icon = getattr(self.book, "cover_icon", None)
        return bool(icon)


@dataclass(frozen=True)
class BookMaturityScoreResult:
    """Score plus the detailed breakdown for UI/tooling."""

    score: int
    components: List[ScoreComponent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "components": [component.__dict__ for component in self.components],
        }


class BookMaturityScoreService:
    """Pure calculator that outputs 0-100 maturity score with reasons."""

    def calculate(self, score_input: BookMaturityScoreInput) -> BookMaturityScoreResult:
        snapshot = self._build_plan111_snapshot(score_input)
        total, plan_components = calculate_plan111_score(snapshot)
        components = [self._convert_component(component) for component in plan_components]
        return BookMaturityScoreResult(score=total, components=components)

    def bulk_calculate(self, inputs: Iterable[BookMaturityScoreInput]) -> List[BookMaturityScoreResult]:
        """Utility helper for scripts/jobs needing batch recomputation."""
        return [self.calculate(entry) for entry in inputs]

    def _build_plan111_snapshot(self, score_input: BookMaturityScoreInput) -> Plan111SnapshotInput:
        raw_summary = getattr(score_input.book.summary, "value", "") if getattr(score_input.book, "summary", None) else ""
        summary_text = str(raw_summary or "").strip()
        summary_length = len(summary_text)
        return Plan111SnapshotInput(
            blocks_count=max(score_input.block_count, 0),
            block_type_count=max(score_input.block_type_count, 0),
            todos_count=max(score_input.open_todo_count, 0),
            tags_count=max(score_input.tag_count, 0),
            summary_length=summary_length,
            has_title=score_input.has_title,
            has_summary=score_input.has_summary,
            has_cover_icon=score_input.cover_icon_selected,
            visits_90d=max(score_input.visit_count_90d, 0),
            last_event_at=self._resolve_last_event_at(score_input),
            manual_adjustment=score_input.operations_bonus,
            calculated_at=datetime.now(timezone.utc),
        )

    def _resolve_last_event_at(self, score_input: BookMaturityScoreInput) -> Optional[datetime]:
        if score_input.last_content_edit_at:
            return self._ensure_timezone(score_input.last_content_edit_at)
        fallback = getattr(score_input.book, "last_content_edit_at", getattr(score_input.book, "updated_at", None))
        return self._ensure_timezone(fallback)

    @staticmethod
    def _ensure_timezone(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo:
            return value
        return value.replace(tzinfo=timezone.utc)

    @staticmethod
    def _convert_component(component: Plan111ScoreComponent) -> ScoreComponent:
        return ScoreComponent(factor=component.factor, points=component.points, detail=component.detail)
