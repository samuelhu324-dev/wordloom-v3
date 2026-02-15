"""GetBlock UseCase - Get a block by ID

This use case handles:
- Validating block exists
- Returning Block domain object
"""

from uuid import UUID

from ...domain import Block
from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ..ports.input import GetBlockRequest
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
    BlockForbiddenError,
    DomainException,
)


class GetBlockUseCase:
    """Get a block by ID"""

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

    async def _assert_block_owner(self, *, block: Block, request: GetBlockRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return

        book = await self.book_repository.get_by_id(block.book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {block.book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: block does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(block.book_id),
                block_id=str(request.block_id),
            )

    async def execute(self, request: GetBlockRequest) -> Block:
        """
        Get block

        Args:
            block_id: Block ID

        Returns:
            Block domain object

        Raises:
            BlockNotFoundError: If block not found
            BlockOperationError: On query error
        """
        try:
            block = await self.repository.get_by_id(request.block_id)
            if not block:
                raise BlockNotFoundError(request.block_id)

            await self._assert_block_owner(block=block, request=request)
            return block
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise BlockOperationError(f"Failed to get block: {str(e)}")
