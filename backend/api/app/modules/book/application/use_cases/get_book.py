"""GetBook UseCase - Retrieve a book by ID

Aligns with input port interface (expects GetBookRequest) and router pattern
that passes a request object instead of raw UUID.
"""

from typing import Optional
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...application.ports.input import GetBookRequest
from ...exceptions import (
    BookNotFoundError,
    BookOperationError,
    BookForbiddenError,
    BookLibraryAssociationError,
    DomainException,
)
from api.app.modules.library.application.ports.output import ILibraryRepository


class GetBookUseCase:
    """Use case: Get Book by ID (excludes soft-deleted)"""

    def __init__(self, repository: BookRepository, *, library_repository: Optional[ILibraryRepository] = None):
        self.repository = repository
        self.library_repository = library_repository

    async def execute(self, request: GetBookRequest) -> Book:
        """Execute retrieval using request DTO.

        Args:
            request: GetBookRequest containing book_id

        Returns:
            Book domain aggregate

        Raises:
            BookNotFoundError: Book missing or soft-deleted
            BookOperationError: Any unexpected repository failure
        """
        try:
            book = await self.repository.get_by_id(request.book_id)
            if not book:
                raise BookNotFoundError(str(request.book_id))

            await self._enforce_library_owner(getattr(book, "library_id", None), request)

            return book
        except Exception as e:
            if isinstance(e, (DomainException, BookNotFoundError)):
                raise
            raise BookOperationError(f"Failed to get book: {e}")

    async def _enforce_library_owner(self, library_id: Optional[UUID], request: GetBookRequest) -> None:
        if not getattr(request, "enforce_owner_check", True) or getattr(request, "actor_user_id", None) is None:
            return
        if self.library_repository is None:
            raise BookOperationError("library_repository is required when enforcing owner checks")
        if library_id is None:
            raise BookLibraryAssociationError(library_id="(missing)", book_id=str(request.book_id), reason="Book has no library_id")

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookLibraryAssociationError(library_id=str(library_id), book_id=str(request.book_id), reason="Library not found")
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookForbiddenError(
                book_id=str(request.book_id),
                library_id=str(library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )
