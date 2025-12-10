"""GetBook UseCase - Retrieve a book by ID

Aligns with input port interface (expects GetBookRequest) and router pattern
that passes a request object instead of raw UUID.
"""

from ...domain import Book
from ...application.ports.output import BookRepository
from ...application.ports.input import GetBookRequest
from ...exceptions import BookNotFoundError, BookOperationError


class GetBookUseCase:
    """Use case: Get Book by ID (excludes soft-deleted)"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

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
                raise BookNotFoundError(request.book_id)
            return book
        except Exception as e:
            if isinstance(e, BookNotFoundError):
                raise
            raise BookOperationError(f"Failed to get book: {e}")
