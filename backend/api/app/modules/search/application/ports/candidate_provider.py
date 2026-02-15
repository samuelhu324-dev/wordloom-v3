"""Stage1 candidate provider port (two-stage search).

This is intentionally a separate port from SearchPort so we don't pollute or
change the existing global search contract.

Stage1 responsibility: cheap recall of candidate entity IDs.
Stage2 responsibility: strict business joins/filters in Postgres.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol
from uuid import UUID


@dataclass(frozen=True)
class Candidate:
    entity_id: UUID
    order_key: int
    snippet: str = ""
    score: Optional[float] = None


class CandidateProvider(Protocol):
    async def get_block_candidates(
        self,
        *,
        q: str,
        candidate_limit: int,
    ) -> list[Candidate]:
        ...


__all__ = [
    "Candidate",
    "CandidateProvider",
]
