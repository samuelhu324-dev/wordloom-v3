"""CreateBlock UseCase - Create a new block (various types)

This use case handles:
- Validating book exists
- Creating Block domain object for different types (TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE)
- Computing fractional index for ordering
- Persisting via repository
"""

from typing import Optional, Dict, Any
from uuid import UUID

from ...domain import Block, BlockType
from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ...exceptions import (
    BlockOperationError,
    BlockForbiddenError,
    DomainException,
)
from ..ports.input import CreateBlockRequest


class CreateBlockUseCase:
    """Create a new block"""

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

    async def _assert_book_owner(
        self,
        *,
        book_id: UUID,
        actor_user_id: UUID | None,
        enforce_owner_check: bool,
    ) -> None:
        if not enforce_owner_check or actor_user_id is None:
            return
        book = await self.book_repository.get_by_id(book_id)
        if not book:
            # Keep legacy behavior: surface as operation error
            raise BlockOperationError(f"Book not found: {book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: book does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(book_id),
            )

    async def execute(self, request: CreateBlockRequest) -> Block:
        """
        Create block

        Args:
            book_id: Book ID
            block_type: Type of block (TEXT, IMAGE, VIDEO, AUDIO, PDF, CODE)
            content: Block content
            metadata: Additional metadata (dimensions for images, duration for videos, etc.)
            position_after_id: Position this block after another block (for fractional indexing)

        Returns:
            Created Block domain object

        Raises:
            BlockOperationError: On persistence error
        """
        try:
            # NOTE:
            # - The current domain factory `Block.create(...)` does not accept `metadata`.
            # - For HEADING blocks, domain requires `heading_level`.

            metadata = request.metadata

            await self._assert_book_owner(
                book_id=request.book_id,
                actor_user_id=getattr(request, "actor_user_id", None),
                enforce_owner_check=getattr(request, "enforce_owner_check", True),
            )

            raw_block_type = request.block_type
            if isinstance(raw_block_type, BlockType):
                block_type = raw_block_type
            else:
                block_type = BlockType(str(raw_block_type).strip().lower())

            heading_level: Optional[int] = None
            if metadata and isinstance(metadata, dict):
                raw_heading_level = metadata.get("heading_level")
                if raw_heading_level is not None:
                    try:
                        heading_level = int(raw_heading_level)
                    except (TypeError, ValueError):
                        heading_level = None

            # TODO: implement fractional ordering once the algorithm is defined.
            # For now, rely on the domain default order.
            _ = request.position_after_id

            block = Block.create(
                book_id=request.book_id,
                block_type=block_type,
                content=request.content or "",
                heading_level=heading_level,
            )
            created_block = await self.repository.save(block)
            return created_block

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            raise BlockOperationError(f"Failed to create block: {str(e)}")
