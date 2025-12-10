"""UpdateLibrary UseCase - Partial update of Library metadata

Supports updating:
  - name
  - description
  - cover_media_id

Multi-Library mode (Migration 002): user can own multiple libraries.
Validation of name/description length handled in Pydantic schemas.
"""

from uuid import UUID
from typing import Optional
from api.app.modules.library.domain import Library, LibraryName
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.library.exceptions import LibraryNotFoundError, InvalidLibraryNameError, LibraryException


class UpdateLibraryRequest:
    def __init__(
        self,
        library_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        cover_media_id: Optional[UUID] = None,
        cover_media_id_provided: bool = False,
        theme_color: Optional[str] = None,
        theme_color_provided: bool = False,
        pinned: Optional[bool] = None,
        pinned_order: Optional[int] = None,
        archived: Optional[bool] = None,
    ):
        self.library_id = library_id
        self.name = name
        self.description = description
        self.cover_media_id = cover_media_id
        self.cover_media_id_provided = cover_media_id_provided
        self.theme_color = theme_color
        self.theme_color_provided = theme_color_provided
        self.pinned = pinned
        self.pinned_order = pinned_order
        self.archived = archived


class UpdateLibraryResponse:
    def __init__(
        self,
        library_id: UUID,
        user_id: UUID,
        name: str,
        description: Optional[str],
        cover_media_id: Optional[UUID],
        created_at,
        updated_at,
        basement_bookshelf_id: Optional[UUID],
        pinned: bool,
        pinned_order: Optional[int],
        archived_at,
        last_activity_at,
        views_count: int,
        last_viewed_at,
        theme_color: Optional[str],
    ):
        self.library_id = library_id
        self.user_id = user_id
        self.name = name
        self.description = description
        self.cover_media_id = cover_media_id
        self.created_at = created_at
        self.updated_at = updated_at
        self.basement_bookshelf_id = basement_bookshelf_id
        self.pinned = pinned
        self.pinned_order = pinned_order
        self.archived_at = archived_at
        self.last_activity_at = last_activity_at
        self.views_count = views_count
        self.last_viewed_at = last_viewed_at
        self.theme_color = theme_color


class UpdateLibraryUseCase:
    def __init__(self, repository: ILibraryRepository):
        self.repository = repository

    async def execute(self, request: UpdateLibraryRequest) -> UpdateLibraryResponse:
        library = await self.repository.get_by_id(request.library_id)
        if not library:
            raise LibraryNotFoundError(str(request.library_id))

        # Apply updates
        if request.name is not None:
            try:
                library.rename(request.name)
            except ValueError as e:
                raise InvalidLibraryNameError(str(e))

        if request.description is not None:
            library.update_description(request.description)

        if request.cover_media_id_provided:
            library.set_cover_media(request.cover_media_id)

        if request.theme_color_provided:
            library.set_theme_color(request.theme_color)

        if request.pinned is not None:
            library.set_pinned(request.pinned, request.pinned_order)
        elif request.pinned_order is not None and library.pinned:
            library.set_pinned(True, request.pinned_order)

        if request.archived is True:
            library.archive()
        elif request.archived is False:
            library.unarchive()

        # Persist
        await self.repository.save(library)

        return UpdateLibraryResponse(
            library_id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            description=library.description,
            cover_media_id=library.cover_media_id,
            created_at=library.created_at,
            updated_at=library.updated_at,
            basement_bookshelf_id=library.basement_bookshelf_id,
            pinned=library.pinned,
            pinned_order=library.pinned_order,
            archived_at=library.archived_at,
            last_activity_at=library.last_activity_at,
            views_count=library.views_count,
            last_viewed_at=library.last_viewed_at,
            theme_color=library.theme_color,
        )
