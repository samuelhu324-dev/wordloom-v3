"""GetBasement UseCase - Get Basement bookshelf

This use case handles:
- Querying for the special Basement bookshelf
- Creating if not exists
- Returning Bookshelf domain object

RULE-010: Every library has exactly one Basement bookshelf
"""

from api.app.modules.bookshelf.application.ports.input import GetBasementRequest
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import Bookshelf
from api.app.modules.bookshelf.exceptions import (
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfOperationError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class GetBasementUseCase:
    """Get the Basement bookshelf (creates if needed)"""

    def __init__(
        self,
        repository: IBookshelfRepository,
        *,
        library_repository: ILibraryRepository | None = None,
    ):
        self.repository = repository
        self.library_repository = library_repository

    async def execute(self, request: GetBasementRequest) -> Bookshelf:
        """
        Get Basement bookshelf

        Args:
            request: GetBasementRequest

        Returns:
            Basement Bookshelf domain object

        Raises:
            BookshelfOperationError: On persistence error
        """
        await self._enforce_library_owner(request)

        try:
            basement = await self.repository.get_basement_by_library_id(request.library_id)
            if basement:
                return basement

            new_basement = Bookshelf.create_basement(library_id=request.library_id)
            await self.repository.save(new_basement)
            created = await self.repository.get_basement_by_library_id(request.library_id)
            if not created:
                raise BookshelfOperationError(
                    bookshelf_id=str(new_basement.id),
                    operation="create_basement",
                    reason="Failed to persist Basement bookshelf",
                )
            return created

        except Exception as exc:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="get_basement",
                reason=str(exc),
                original_error=exc,
            ) from exc

    async def _enforce_library_owner(self, request: GetBasementRequest) -> None:
        if not request.enforce_owner_check or request.actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="authorize",
                reason="library_repository is required when enforcing owner checks",
            )

        library = await self.library_repository.get_by_id(request.library_id)
        if not library:
            raise BookshelfLibraryAssociationError(
                bookshelf_id="<unknown>",
                library_id=str(request.library_id),
                reason="Library not found",
            )
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookshelfForbiddenError(
                library_id=str(request.library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )
