from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RequestContext:
    """Request-scoped context for observability.

    Keep this in `api.app.shared` so routers/use-cases/adapters can share it,
    while domain remains infrastructure-agnostic.
    """

    correlation_id: str
    actor_id: Optional[UUID] = None
    workspace_id: Optional[UUID] = None
    route: Optional[str] = None
    method: Optional[str] = None
