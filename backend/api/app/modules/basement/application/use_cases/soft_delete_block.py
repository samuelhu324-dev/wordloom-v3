"""SoftDeleteBlockUseCase wrapper."""
from __future__ import annotations

from api.app.modules.block.application.ports.output import BlockRepository
from api.app.modules.block.application.use_cases.delete_block import DeleteBlockUseCase
from api.app.modules.block.domain import Block

from ..dtos import SoftDeleteBlockCommand


class SoftDeleteBlockUseCase:
    """Reuse block Delete use case but expose it through Basement module."""

    def __init__(self, repository: BlockRepository):
        self._delegate = DeleteBlockUseCase(repository)

    async def execute(self, command: SoftDeleteBlockCommand) -> Block:
        return await self._delegate.execute(block_id=command.block_id, book_id=command.book_id)
