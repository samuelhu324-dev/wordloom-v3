"""Plan111 maturity scoring helpers shared across modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass(frozen=True)
class Plan111ScoreComponent:
    """Structure describing how many points a factor contributed."""

    factor: str
    points: int
    detail: str


@dataclass(frozen=True)
class Plan111StructureTaskBlueprint:
    """Lightweight definition for structure tasks used by Plan111."""

    code: str
    title: str
    description: str
    required_stage: str
    points: int = 5


@dataclass(frozen=True)
class Plan111SnapshotInput:
    """Normalized signals consumed by the Plan111 rule set."""

    blocks_count: int
    block_type_count: int
    todos_count: int
    tags_count: int
    summary_length: int
    has_title: bool
    has_summary: bool
    has_cover_icon: bool
    visits_90d: int
    last_event_at: Optional[datetime] = None
    manual_adjustment: int = 0
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


PLAN111_STRUCTURE_TASKS: List[Plan111StructureTaskBlueprint] = [
    Plan111StructureTaskBlueprint(
        code="long_summary",
        title="扩写摘要到 120 字",
        description="摘要达到 120 字即可视为“记录完整背景”",
        required_stage="growing",
        points=5,
    ),
    Plan111StructureTaskBlueprint(
        code="tag_landscape",
        title="配置至少 3 个标签",
        description="丰富标签体系方便书架检索",
        required_stage="growing",
        points=5,
    ),
    Plan111StructureTaskBlueprint(
        code="outline_depth",
        title="保持 15+ Blocks 且类型不少于 4 种",
        description="结构均衡才能迈向 Stable",
        required_stage="stable",
        points=5,
    ),
    Plan111StructureTaskBlueprint(
        code="todo_zero",
        title="清空关键 TODO",
        description="TODO 清零后才能视为结构巩固",
        required_stage="stable",
        points=5,
    ),
]


def calculate_plan111_score(snapshot: Plan111SnapshotInput) -> tuple[int, List[Plan111ScoreComponent]]:
    """Return the clamped score plus its contributing components."""

    components: List[Plan111ScoreComponent] = []
    total = 0

    def add(points: int, factor: str, detail: str) -> None:
        nonlocal total
        if points == 0:
            return
        components.append(Plan111ScoreComponent(factor=factor, points=points, detail=detail))
        total += points

    # Structure (0-30)
    if snapshot.has_title:
        add(5, "structure_title", "结构：已填写标题")
    if snapshot.has_summary and snapshot.summary_length >= 40:
        add(5, "structure_summary", "结构：摘要不少于 40 字")
    if snapshot.tags_count >= 1:
        add(5, "structure_tags", "结构：至少 1 个标签")
    if snapshot.has_cover_icon:
        add(5, "structure_cover", "结构：已配置封面图标")
    if snapshot.blocks_count >= 10:
        add(10, "structure_blocks", "结构：Block 数 ≥ 10")
    elif snapshot.blocks_count >= 3:
        add(5, "structure_blocks", "结构：Block 数 ≥ 3")

    # Activity (0-30)
    add(_recent_edit_points(snapshot), "activity_recent_edit", _recent_edit_detail(snapshot))
    add(_visit_points(snapshot.visits_90d), "activity_visits", _visit_detail(snapshot.visits_90d))
    todo_points, todo_detail = _todo_health(snapshot.todos_count)
    add(todo_points, "activity_todo_health", todo_detail)

    # Quality (0-20)
    add(*_block_variety_component(snapshot.block_type_count))
    add(*_outline_depth_component(snapshot.blocks_count, snapshot.summary_length))

    # Structure tasks (0-20)
    for blueprint in PLAN111_STRUCTURE_TASKS:
        if is_plan111_task_completed(blueprint.code, snapshot):
            add(blueprint.points, f"task_{blueprint.code}", f"结构任务：{blueprint.title}")

    # Manual adjustment (-5 ~ +5)
    manual = max(-5, min(5, snapshot.manual_adjustment))
    if manual:
        direction = "加成" if manual > 0 else "扣分"
        add(manual, "manual_adjustment", f"人工{direction} {manual} 分")

    total = max(0, min(total, 100))
    return total, components


def _recent_edit_points(snapshot: Plan111SnapshotInput) -> int:
    if not snapshot.last_event_at:
        return 0
    delta = snapshot.calculated_at - snapshot.last_event_at
    days = delta.days if delta.days >= 0 else 0
    if days <= 30:
        return 10
    if days <= 60:
        return 5
    return 0


def _recent_edit_detail(snapshot: Plan111SnapshotInput) -> str:
    if not snapshot.last_event_at:
        return "活动：暂无编辑记录"
    delta = snapshot.calculated_at - snapshot.last_event_at
    days = max(delta.days, 0)
    if days <= 30:
        return "活动：30 天内有编辑"
    if days <= 60:
        return "活动：60 天内有编辑"
    return "活动：超过 60 天无编辑"


def _visit_points(visits_90d: int) -> int:
    if visits_90d >= 10:
        return 10
    if visits_90d >= 3:
        return 6
    if visits_90d >= 1:
        return 3
    return 0


def _visit_detail(visits_90d: int) -> str:
    if visits_90d >= 10:
        return "活动：90 天访问 ≥ 10 次"
    if visits_90d >= 3:
        return "活动：90 天访问 3-9 次"
    if visits_90d >= 1:
        return "活动：90 天访问 1-2 次"
    return "活动：90 天内无访问"


def _todo_health(todos_count: int) -> tuple[int, str]:
    if todos_count <= 0:
        return 10, "活动：TODO 清零"
    if todos_count <= 3:
        return 6, f"活动：剩余 {todos_count} 个 TODO"
    if todos_count <= 5:
        return 3, f"活动：剩余 {todos_count} 个 TODO"
    return 0, "活动：TODO 仍需处理"


def _block_variety_component(block_type_count: int) -> tuple[int, str, str]:
    if block_type_count >= 4:
        return 10, "quality_block_variety", "质量：Block 类型 ≥ 4 种"
    if block_type_count >= 3:
        return 6, "quality_block_variety", "质量：Block 类型 3 种"
    if block_type_count >= 2:
        return 3, "quality_block_variety", "质量：Block 类型 2 种"
    return 0, "quality_block_variety", "质量：Block 类型单一"


def _outline_depth_component(blocks_count: int, summary_length: int) -> tuple[int, str, str]:
    if blocks_count >= 18 and summary_length >= 160:
        return 10, "quality_outline_depth", "质量：Block ≥ 18 且摘要 ≥ 160 字"
    if blocks_count >= 12 and summary_length >= 120:
        return 6, "quality_outline_depth", "质量：结构接近完整"
    if blocks_count >= 8 and summary_length >= 80:
        return 3, "quality_outline_depth", "质量：仍需补充摘要/结构"
    return 0, "quality_outline_depth", "质量：结构与摘要未达标"


def is_plan111_task_completed(code: str, snapshot: Plan111SnapshotInput) -> bool:
    match code:
        case "long_summary":
            return snapshot.summary_length >= 120
        case "tag_landscape":
            return snapshot.tags_count >= 3
        case "outline_depth":
            return snapshot.blocks_count >= 15 and snapshot.block_type_count >= 4
        case "todo_zero":
            return snapshot.todos_count == 0
        case _:
            return False
