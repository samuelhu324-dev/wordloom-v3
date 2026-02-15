from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
from uuid import UUID


@dataclass(frozen=True)
class Actor:
    """Authenticated request actor (authn output).

    This is intentionally minimal for now. We will extend it later with
    memberships/roles and tenant/workspace selection.
    """

    user_id: UUID
    workspace_id: Optional[UUID] = None
    roles: Tuple[str, ...] = ()
