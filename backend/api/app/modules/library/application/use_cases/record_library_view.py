"""RecordLibraryView UseCase - persist view counters immediately."""

import logging

from api.app.modules.library.application.ports.input import (
    RecordLibraryViewRequest,
    RecordLibraryViewResponse,
    IRecordLibraryViewUseCase,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.library.exceptions import LibraryNotFoundError

logger = logging.getLogger(__name__)


class RecordLibraryViewUseCase(IRecordLibraryViewUseCase):
    """Increment the view counter and persist last viewed timestamp."""

    def __init__(self, repository: ILibraryRepository):
        self.repository = repository

    async def execute(self, request: RecordLibraryViewRequest) -> RecordLibraryViewResponse:
        logger.debug("Recording library view", extra={"library_id": str(request.library_id)})
        library = await self.repository.get_by_id(request.library_id)
        if not library:
            raise LibraryNotFoundError(str(request.library_id))

        library.record_view()
        await self.repository.save(library)

        return RecordLibraryViewResponse(
            library_id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            description=library.description,
            cover_media_id=library.cover_media_id,
            basement_bookshelf_id=library.basement_bookshelf_id,
            created_at=library.created_at,
            updated_at=library.updated_at,
            pinned=library.pinned,
            pinned_order=library.pinned_order,
            archived_at=library.archived_at,
            last_activity_at=library.last_activity_at,
            views_count=library.views_count,
            last_viewed_at=library.last_viewed_at,
            theme_color=getattr(library, "theme_color", None),
        )
