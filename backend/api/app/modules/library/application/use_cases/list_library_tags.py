"""Use case for loading Plan_31 tag chips for Libraries."""

from __future__ import annotations

import logging

from typing import Dict, List
from uuid import UUID

from api.app.modules.library.application.ports.input import (
    IListLibraryTagsUseCase,
    ListLibraryTagsRequest,
    ListLibraryTagsResponse,
    LibraryTagChipDTO,
)
from api.app.modules.library.application.ports.output import ILibraryTagAssociationRepository

logger = logging.getLogger(__name__)


class ListLibraryTagsUseCase(IListLibraryTagsUseCase):
    """Fetch limited tag chips plus totals for a batch of Libraries."""

    def __init__(self, repository: ILibraryTagAssociationRepository):
        self.repository = repository

    async def execute(self, request: ListLibraryTagsRequest) -> ListLibraryTagsResponse:
        if not request.library_ids:
            return ListLibraryTagsResponse(tag_map={}, tag_totals={})

        logger.debug(
            "ListLibraryTagsUseCase start", extra={
                "library_count": len(request.library_ids),
                "limit": request.limit_per_library,
            }
        )

        raw_dtos = await self.repository.fetch_option_a_tags(
            request.library_ids,
            limit_per_library=request.limit_per_library,
        )

        tag_map: Dict[UUID, List[LibraryTagChipDTO]] = {}
        for dto in raw_dtos:
            chips = tag_map.setdefault(dto.library_id, [])
            chips.append(
                LibraryTagChipDTO(
                    id=dto.tag_id,
                    name=dto.tag_name,
                    color=dto.tag_color,
                    description=dto.tag_description,
                )
            )

        totals = await self.repository.count_tags_by_library(request.library_ids)

        tag_id_map: Dict[UUID, List[UUID]] = {}
        if request.include_tag_ids:
            for lib_id in request.library_ids:
                tag_id_map[lib_id] = await self.repository.list_tag_ids(lib_id)

        logger.debug(
            "ListLibraryTagsUseCase finish",
            extra={"tagged_libraries": len(tag_map)},
        )

        return ListLibraryTagsResponse(
            tag_map=tag_map,
            tag_totals=totals,
            tag_id_map=tag_id_map,
        )
