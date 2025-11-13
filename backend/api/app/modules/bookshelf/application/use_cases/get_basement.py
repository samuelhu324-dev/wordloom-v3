"""GetBasement UseCase - Get Basement bookshelf

This use case handles:
- Querying for the special Basement bookshelf
- Creating if not exists
- Returning Bookshelf domain object

RULE-010: Every library has exactly one Basement bookshelf
"""

from uuid import UUID

from ...domain import Bookshelf
from ...application.ports.output import BookshelfRepository
from ...exceptions import (
    BookshelfNotFoundError,
    BookshelfOperationError,
)


class GetBasementUseCase:
    """Get the Basement bookshelf (creates if needed)"""

    def __init__(self, repository: BookshelfRepository):
        self.repository = repository

    async def execute(self, library_id: UUID) -> Bookshelf:
        """
        Get Basement bookshelf

        Args:
            library_id: Library ID

        Returns:
            Basement Bookshelf domain object

        Raises:
            BookshelfOperationError: On persistence error
        """
        try:
            basement = await self.repository.get_basement_by_library_id(library_id)
            if basement:
                return basement

            # Create Basement if not exists
            new_basement = Bookshelf.create_basement(library_id=library_id)
            created_basement = await self.repository.save(new_basement)
            return created_basement

        except Exception as e:
            raise BookshelfOperationError(f"Failed to get/create Basement: {str(e)}")
