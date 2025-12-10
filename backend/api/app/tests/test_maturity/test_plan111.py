"""Unit tests for Plan111 scoring helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from api.app.modules.book.domain.services.plan111 import Plan111SnapshotInput, calculate_plan111_score


def _snapshot(**overrides) -> Plan111SnapshotInput:
    now = datetime.now(timezone.utc)
    base = dict(
        blocks_count=0,
        block_type_count=0,
        todos_count=0,
        tags_count=0,
        summary_length=0,
        has_title=False,
        has_summary=False,
        has_cover_icon=False,
        visits_90d=0,
        last_event_at=now - timedelta(days=90),
        manual_adjustment=0,
        calculated_at=now,
    )
    base.update(overrides)
    return Plan111SnapshotInput(**base)


def _sum_factor(components, prefix: str) -> int:
    return sum(item.points for item in components if item.factor.startswith(prefix))


def test_structure_category_caps_at_thirty() -> None:
    snapshot = _snapshot(
        has_title=True,
        has_summary=True,
        summary_length=80,
        tags_count=2,
        has_cover_icon=True,
        blocks_count=12,
    )

    score, components = calculate_plan111_score(snapshot)

    assert _sum_factor(components, "structure") == 30
    assert score >= 30


def test_activity_rewards_recency_visits_and_todo_health() -> None:
    snapshot = _snapshot(
        last_event_at=datetime.now(timezone.utc) - timedelta(days=5),
        visits_90d=12,
        todos_count=0,
    )

    _, components = calculate_plan111_score(snapshot)

    assert _sum_factor(components, "activity") == 30


def test_structure_tasks_grant_twenty_points_when_all_done() -> None:
    snapshot = _snapshot(
        summary_length=200,
        tags_count=5,
        blocks_count=20,
        block_type_count=4,
        todos_count=0,
    )

    _, components = calculate_plan111_score(snapshot)

    assert _sum_factor(components, "task_") == 20
