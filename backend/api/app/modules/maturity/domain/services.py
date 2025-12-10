"""Domain services for maturity computations."""
from __future__ import annotations

from typing import Iterable, List, Optional

from dataclasses import dataclass
from typing import Iterable, List, Optional

from api.app.modules.book.domain.services import (
    BookMaturityScoreInput,
    BookMaturityScoreService,
)
from api.app.modules.book.application.utils.maturity import derive_maturity_from_score

from .models import (
    MaturityScore,
    ScoreComponent,
    MaturitySignals,
    MaturityStage,
    TransitionTask,
)


class MaturityRuleEngine:
    """High-level facade around the existing book maturity score service."""

    def __init__(self, score_service: Optional[BookMaturityScoreService] = None) -> None:
        self._score_service = score_service or BookMaturityScoreService()

    def evaluate(self, payload: BookMaturityScoreInput) -> MaturityScore:
        result = self._score_service.calculate(payload)
        return MaturityScore(
            value=result.score,
            components=[ScoreComponent(**component.__dict__) for component in result.components],
        )

    def bulk_evaluate(self, payloads: Iterable[BookMaturityScoreInput]) -> List[MaturityScore]:
        return [self.evaluate(payload) for payload in payloads]

    @staticmethod
    def derive_stage(score_value: int) -> MaturityStage:
        book_stage = derive_maturity_from_score(score_value)
        return MaturityStage(book_stage.value)


class MaturityTransitionPolicy:
    """Light-weight policy that provides actionable graduation tasks."""

    TASK_LIBRARY = {
        "add_summary": TransitionTask(
            code="add_summary",
            title="补全摘要",
            description="填写精炼摘要可以让 Book 更容易被检索和复习",
            weight=2,
        ),
        "add_tags": TransitionTask(
            code="add_tags",
            title="补齐标签",
            description="至少关联 1 个标签帮助系统归类",
            weight=1,
        ),
        "add_cover": TransitionTask(
            code="add_cover",
            title="选择封面图标",
            description="Lucide 封面图标用于视觉识别成熟内容",
            weight=1,
        ),
        "add_blocks": TransitionTask(
            code="add_blocks",
            title="补充 Block 内容",
            description="增加 Block 数量与类型能够提升成熟度",
            weight=2,
        ),
        "close_todos": TransitionTask(
            code="close_todos",
            title="清收 TODO",
            description="处理未完成 TODO 可以恢复 20 分守门得分",
            weight=2,
        ),
    }

    def _task(self, code: str) -> TransitionTask:
        template = self.TASK_LIBRARY[code]
        return TransitionTask(
            code=template.code,
            title=template.title,
            description=template.description,
            weight=template.weight,
        )

    def recommend(self, score: MaturityScore, signals: MaturitySignals) -> List[TransitionTask]:
        suggestions: List[TransitionTask] = []

        if not signals.has_summary:
            suggestions.append(self._task("add_summary"))
        if not signals.has_tags:
            suggestions.append(self._task("add_tags"))
        if not signals.has_cover:
            suggestions.append(self._task("add_cover"))
        if signals.block_count < 5 or signals.block_type_count < 3:
            suggestions.append(self._task("add_blocks"))
        if signals.open_todos >= 5:
            suggestions.append(self._task("close_todos"))

        # If score already high, trim to the most relevant two tasks
        if score.value >= 70 and suggestions:
            suggestions = sorted(suggestions, key=lambda task: task.weight, reverse=True)[:2]

        return suggestions
