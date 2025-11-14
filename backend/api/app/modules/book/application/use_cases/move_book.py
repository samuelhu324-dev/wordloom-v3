"""
MoveBook UseCase - Transfer a book to another bookshelf

Implements RULE-011: Book Transfer Operation

This use case handles:
- Validating source book exists
- Validating target bookshelf exists
- Performing cross-bookshelf transfer
- Emitting BookMovedToBookshelf event
- Persisting changes via repository
"""

from uuid import UUID
import logging

from ...domain import Book
from ..ports.input import (
    MoveBookRequest,
    BookResponse,
)
from ..ports.output import BookRepository
from ...exceptions import (
    BookNotFoundError,
    InvalidBookMoveError,
)

logger = logging.getLogger(__name__)


class MoveBookUseCase:
    """Transfer a book to another bookshelf (RULE-011)"""

    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def execute(self, request: MoveBookRequest) -> BookResponse:
        """
        Move a book to a different bookshelf

        RULE-011: Books can move across bookshelves.
        Domain method: move_to_bookshelf()

        Args:
            request: MoveBookRequest containing:
                - book_id: UUID (the book to move)
                - target_bookshelf_id: UUID (destination bookshelf)
                - reason: Optional[str] (audit trail)

        Returns:
            BookResponse with updated bookshelf_id

        Raises:
            BookNotFoundError: If book doesn't exist
            InvalidBookMoveError: If move is invalid (same shelf, etc.)
        """
        try:
            # Fetch the book
            logger.debug(f"MoveBookUseCase: Fetching book {request.book_id}")
            book = await self.repository.get_by_id(request.book_id)
            if not book:
                logger.warning(f"Book not found: {request.book_id}")
                raise BookNotFoundError(f"Book {request.book_id} not found")

            # Validate move (throws ValueError if invalid)
            logger.info(f"MoveBookUseCase: Moving book {book.id} from {book.bookshelf_id} to {request.target_bookshelf_id}")

            # Call domain method which performs transfer and emits event
            book.move_to_bookshelf(request.target_bookshelf_id)

            # Persist the changes
            updated_book = await self.repository.save(book)
            logger.info(f"MoveBookUseCase: Book moved successfully: {updated_book.id}")

            # Publish events (Infrastructure layer responsibility)
            # Events are already in book.events from domain method

            return BookResponse.from_domain(updated_book)

        except BookNotFoundError:
            raise
        except ValueError as e:
            logger.warning(f"Invalid move operation: {e}")
            raise InvalidBookMoveError(str(e))
        except Exception as e:
            logger.error(f"Unexpected error in MoveBookUseCase: {e}", exc_info=True)
            raise InvalidBookMoveError(f"Failed to move book: {str(e)}")
