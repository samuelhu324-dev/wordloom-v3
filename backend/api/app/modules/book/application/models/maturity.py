"""Shared dataclasses for Book maturity orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ...domain.services import ScoreComponent


@dataclass
class PartitionMigrationResult:
    """Represents a single maturity partition change."""

    book_id: UUID
    from_maturity: str
    to_maturity: str
    score: int
    trigger: str
    is_manual_override: bool
    occurred_at: datetime


@dataclass
class BookMaturityMutationResult:
    """Return value for maturity-related use cases."""

    book_id: UUID
    maturity: str
    maturity_score: int
    manual_override: bool
    partition_migration: Optional[PartitionMigrationResult] = None
    score_components: Optional[List[ScoreComponent]] = None