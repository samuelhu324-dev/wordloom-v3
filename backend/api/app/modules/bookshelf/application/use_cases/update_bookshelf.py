"""UpdateBookshelf UseCase - Update bookshelf properties

This use case handles:
- Validating bookshelf exists
- Updating name (with uniqueness check per library)
- Updating description and color
- Persisting via repository
"""

from typing import Optional
from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import (
    BookshelfNotFoundError,
    BookshelfAlreadyExistsError,
    BookshelfOperationError,
)


class UpdateBookshelfUseCase:
    """Update bookshelf properties"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(
        self,
        bookshelf_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None
    ) -> Bookshelf:
        """
        Update bookshelf

        Args:
            bookshelf_id: Bookshelf ID
            name: New name (optional)
            description: New description (optional)
            color: New color (optional)

        Returns:
            Updated Bookshelf domain object

        Raises:
            BookshelfNotFoundError: If bookshelf not found
            BookshelfAlreadyExistsError: If new name already exists
            BookshelfOperationError: On persistence error
        """
        bookshelf = await self.repository.get_by_id(bookshelf_id)
        if not bookshelf:
            raise BookshelfNotFoundError(bookshelf_id)

        try:
            if name is not None and name != bookshelf.name:
                # Check uniqueness in library
                if await self.repository.exists_by_name(bookshelf.library_id, name, exclude_id=bookshelf_id):
                    raise BookshelfAlreadyExistsError(name, bookshelf.library_id)
                bookshelf.rename(name)

            if description is not None:
                bookshelf.set_description(description)

            if color is not None:
                bookshelf.set_color(color)

            updated_bookshelf = await self.repository.save(bookshelf)
            return updated_bookshelf

        except Exception as e:
            if isinstance(e, (BookshelfNotFoundError, BookshelfAlreadyExistsError)):
                raise
            raise BookshelfOperationError(f"Failed to update bookshelf: {str(e)}")
