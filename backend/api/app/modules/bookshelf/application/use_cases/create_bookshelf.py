"""CreateBookshelf UseCase - Create a new bookshelf

This use case handles:
- Validating library exists
- Validating bookshelf name is unique within library
- Creating Bookshelf domain object
- Persisting via repository

RULE-006: Bookshelf name must be unique per library
RULE-010: Basement is auto-created per library, cannot be created manually
"""

from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import (
    BookshelfAlreadyExistsError,
    BookshelfOperationError,
)


class CreateBookshelfUseCase:
    """Create a new bookshelf"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(
        self,
        library_id: UUID,
        name: str,
        description: str = None,
        color: str = None
    ) -> Bookshelf:
        """
        Create bookshelf

        Args:
            library_id: Library ID
            name: Bookshelf name (must be unique within library)
            description: Optional description
            color: Optional color

        Returns:
            Created Bookshelf domain object

        Raises:
            BookshelfAlreadyExistsError: If name already exists in library
            BookshelfOperationError: On persistence error
        """
        # Check name uniqueness per library
        if await self.repository.exists_by_name(library_id, name):
            raise BookshelfAlreadyExistsError(name, library_id)

        try:
            bookshelf = Bookshelf.create(
                library_id=library_id,
                name=name,
                description=description,
                color=color
            )
            created_bookshelf = await self.repository.save(bookshelf)
            return created_bookshelf

        except Exception as e:
            if isinstance(e, BookshelfAlreadyExistsError):
                raise
            raise BookshelfOperationError(f"Failed to create bookshelf: {str(e)}")
