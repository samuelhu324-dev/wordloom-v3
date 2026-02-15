"""ReorderBlocks UseCase - Fractional index based ordering."""

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from ...application.ports.input import (
    BlockResponse,
    ReorderBlocksRequest,
)
from ...application.ports.output import BlockRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
    FractionalIndexError,
    BlockForbiddenError,
)


class ReorderBlocksUseCase:
    """Reorder blocks using fractional indexing."""

    def __init__(
        self,
        repository: BlockRepository,
        *,
        book_repository: BookRepository,
        library_repository: ILibraryRepository,
        event_bus=None,
    ):
        self.repository = repository
        self.book_repository = book_repository
        self.library_repository = library_repository
        self.event_bus = event_bus

    async def _assert_block_owner(self, *, book_id, request: ReorderBlocksRequest) -> None:
        if not getattr(request, "enforce_owner_check", True):
            return
        actor_user_id = getattr(request, "actor_user_id", None)
        if actor_user_id is None:
            return
        book = await self.book_repository.get_by_id(book_id)
        if not book:
            raise BlockOperationError(f"Book not found: {book_id}")
        library = await self.library_repository.get_by_id(book.library_id)
        if not library:
            raise BlockOperationError(f"Library not found: {book.library_id}")
        if library.user_id != actor_user_id:
            raise BlockForbiddenError(
                "Forbidden: block does not belong to actor",
                actor_user_id=str(actor_user_id),
                library_id=str(book.library_id),
                book_id=str(book_id),
                block_id=str(request.block_id),
            )

    async def execute(self, request: ReorderBlocksRequest) -> BlockResponse:
        """Handle /blocks/reorder payloads."""

        block = await self.repository.get_by_id(request.block_id)
        if not block:
            raise BlockNotFoundError(str(request.block_id))

        await self._assert_block_owner(book_id=block.book_id, request=request)

        try:
            new_order, prev_order, next_order = await self._resolve_new_order(request, block.book_id)
        except (BlockNotFoundError, FractionalIndexError):
            raise
        except Exception as exc:  # pragma: no cover - defensive guardrail
            raise BlockOperationError(
                message="Failed to compute new order",
                block_id=str(request.block_id),
                operation="reorder",
                reason=str(exc),
                original_error=exc,
            ) from exc

        block.reorder(new_order, prev_order, next_order)
        await self.repository.save(block)

        # Event bus integration can hook into block.events in future phases.
        return BlockResponse.from_domain(block)

    async def _resolve_new_order(
        self,
        request: ReorderBlocksRequest,
        book_id,
    ) -> Tuple[Decimal, Optional[Decimal], Optional[Decimal]]:
        """Determine the target order plus neighbor context."""

        if request.new_order is not None:
            parsed = self._parse_decimal(request.new_order, request.block_id)
            return parsed, None, None

        prev_order = None
        next_order = None

        if request.position_after_id:
            prev_order = await self._load_anchor_order(
                anchor_id=request.position_after_id,
                book_id=book_id,
                relation="after",
            )

        if request.position_before_id:
            next_order = await self._load_anchor_order(
                anchor_id=request.position_before_id,
                book_id=book_id,
                relation="before",
            )

        if prev_order is None and next_order is None:
            raise FractionalIndexError(
                block_id=str(request.block_id),
                reason="new_order missing and no anchor provided",
                current_order=None,
            )

        new_order = self.repository.new_key_between(prev_order, next_order)
        return new_order, prev_order, next_order

    async def _load_anchor_order(self, anchor_id, book_id, relation: str) -> Decimal:
        anchor = await self.repository.get_by_id(anchor_id)
        if not anchor:
            raise BlockNotFoundError(str(anchor_id))
        if anchor.book_id != book_id:
            raise FractionalIndexError(
                block_id=str(anchor_id),
                reason=f"Anchor for {relation} relation belongs to another book",
                current_order=None,
            )
        return anchor.order

    @staticmethod
    def _parse_decimal(value, block_id) -> Decimal:
        try:
            if isinstance(value, Decimal):
                return value
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            raise FractionalIndexError(
                block_id=str(block_id),
                reason="new_order must be a decimal-compatible value",
                current_order=None,
            )
