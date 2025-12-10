"""Bridge layer for Book↔Basement interactions.

Keeps the Book module from importing Basement routers or DI directly while
still allowing Book use cases to reuse Basement application services.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from api.app.modules.basement.application.dtos import (
    MoveBookToBasementCommand,
    RestoreBookFromBasementCommand,
)
from api.app.modules.basement.application.use_cases.move_book_to_basement import (
    MoveBookToBasementUseCase,
)
from api.app.modules.basement.application.use_cases.restore_book_from_basement import (
    RestoreBookFromBasementUseCase,
)
from api.app.modules.basement.domain.entities import BasementBookSnapshot
from api.app.modules.book.exceptions import BookOperationError


class BookBasementBridge:
    """Orchestrate Basement workflows on behalf of Book use cases."""

    def __init__(
        self,
        *,
        move_book_to_basement_use_case: Optional[MoveBookToBasementUseCase] = None,
        restore_book_from_basement_use_case: Optional[RestoreBookFromBasementUseCase] = None,
    ) -> None:
        self._move_use_case = move_book_to_basement_use_case
        self._restore_use_case = restore_book_from_basement_use_case

    async def move_book_to_basement(
        self,
        *,
        book_id: UUID,
        basement_bookshelf_id: UUID,
        actor_id: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> BasementBookSnapshot:
        if not self._move_use_case:
            raise BookOperationError("Basement move use case is not configured")

        command = MoveBookToBasementCommand(
            book_id=book_id,
            basement_bookshelf_id=basement_bookshelf_id,
            actor_id=actor_id,
            reason=reason,
        )
        return await self._move_use_case.execute(command)

    async def restore_book_from_basement(
        self,
        *,
        book_id: UUID,
        target_bookshelf_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
    ) -> BasementBookSnapshot:
        if not self._restore_use_case:
            raise BookOperationError("Basement restore use case is not configured")

        command = RestoreBookFromBasementCommand(
            book_id=book_id,
            target_bookshelf_id=target_bookshelf_id,
            actor_id=actor_id,
        )
        return await self._restore_use_case.execute(command)
