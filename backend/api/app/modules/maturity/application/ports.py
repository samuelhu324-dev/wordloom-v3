"""Ports for maturity module adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..domain import BookProfileSnapshot, MaturitySnapshot, MaturityStage


class MaturityDataProvider(ABC):
    """Provides normalized snapshots from aggregates."""

    @abstractmethod
    async def load_book_profile(self, book_id: UUID) -> BookProfileSnapshot:
        raise NotImplementedError


class MaturitySnapshotRepository(ABC):
    """Persistence port for maturity snapshots."""

    @abstractmethod
    async def save_snapshot(self, snapshot: MaturitySnapshot) -> MaturitySnapshot:
        raise NotImplementedError

    @abstractmethod
    async def list_snapshots(self, book_id: UUID, limit: int = 10) -> List[MaturitySnapshot]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_stage(self, book_id: UUID) -> Optional[MaturityStage]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_snapshot(self, book_id: UUID) -> Optional[MaturitySnapshot]:
        raise NotImplementedError
