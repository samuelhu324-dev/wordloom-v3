"""ReorderBlocks UseCase - Fractional index based ordering."""

from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

from ...application.ports.input import (
    BlockResponse,
    ReorderBlocksRequest,
)
from ...application.ports.output import BlockRepository
from ...exceptions import (
    BlockNotFoundError,
    BlockOperationError,
    FractionalIndexError,
)


class ReorderBlocksUseCase:
    """Reorder blocks using fractional indexing."""

    def __init__(self, repository: BlockRepository, event_bus=None):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: ReorderBlocksRequest) -> BlockResponse:
        """Handle /blocks/reorder payloads."""

        block = await self.repository.get_by_id(request.block_id)
        if not block:
            raise BlockNotFoundError(str(request.block_id))

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
