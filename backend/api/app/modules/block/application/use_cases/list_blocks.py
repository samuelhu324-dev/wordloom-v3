"""ListBlocks UseCase - List blocks in a book with pagination"""

from ...application.ports.input import (
    BlockListResponse,
    BlockResponse,
    ListBlocksRequest,
)
from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ...exceptions import DomainException, BlockOperationError, BlockForbiddenError


class ListBlocksUseCase:
    """List blocks in a book"""

    def __init__(
        self,
        repository: BlockRepository,
        *,
        book_repository: BookRepository,
        library_repository: ILibraryRepository,
    ):
        self.repository = repository
        self.book_repository = book_repository
        self.library_repository = library_repository

    async def _assert_book_owner(self, request: ListBlocksRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return
        book = await self.book_repository.get_by_id(request.book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {request.book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: book does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(request.book_id),
            )

    async def execute(self, request: ListBlocksRequest) -> BlockListResponse:
        """List blocks with pagination and optional soft-delete filtering"""

        try:
            await self._assert_book_owner(request)
            limit = max(1, request.limit)
            page = max(1, (request.skip // limit) + 1)
            blocks, total = await self.repository.list_paginated(
                book_id=request.book_id,
                page=page,
                page_size=limit,
                include_deleted=request.include_deleted,
            )
            items = [BlockResponse.from_domain(block) for block in blocks]
            return BlockListResponse(items=items, total=total)
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise BlockOperationError(f"Failed to list blocks: {str(e)}")
