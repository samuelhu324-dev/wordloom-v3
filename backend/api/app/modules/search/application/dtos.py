from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BlockSearchHit:
    """Search-only DTO for block hits (does not belong to domain).

    Minimal version for two-stage search:
    - id + tags is the core
    - snippet/score are optional and can be evolved later
    """

    id: UUID
    tags: List[str]
    snippet: Optional[str] = None
    score: Optional[float] = None


__all__ = [
    "BlockSearchHit",
]
