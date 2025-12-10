"""Use case for replacing tag associations on a Library."""

from __future__ import annotations

import logging
from uuid import UUID

from api.app.modules.library.application.ports.input import (
    IReplaceLibraryTagsUseCase,
    ReplaceLibraryTagsRequest,
)
from api.app.modules.library.application.ports.output import ILibraryTagAssociationRepository

logger = logging.getLogger(__name__)


class ReplaceLibraryTagsUseCase(IReplaceLibraryTagsUseCase):
    """Replace existing Library tag associations atomically."""

    def __init__(self, repository: ILibraryTagAssociationRepository):
        self.repository = repository

    async def execute(self, request: ReplaceLibraryTagsRequest) -> None:
        unique_ids: list[UUID] = []
        seen: set[UUID] = set()
        for tag_id in request.tag_ids:
            if tag_id in seen:
                continue
            seen.add(tag_id)
            unique_ids.append(tag_id)

        logger.info(
            "ReplaceLibraryTagsUseCase",
            extra={
                "library_id": str(request.library_id),
                "new_tag_count": len(unique_ids),
            },
        )

        await self.repository.replace_library_tags(
            library_id=request.library_id,
            tag_ids=unique_ids,
            actor_id=request.actor_id,
        )
