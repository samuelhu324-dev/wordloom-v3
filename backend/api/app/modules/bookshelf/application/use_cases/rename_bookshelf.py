"""RenameBookshelf UseCase - Rename an existing Bookshelf

Responsibilities:
- Load bookshelf from repository by ID
- Validate new name (length, format, uniqueness per library)
- Call bookshelf.rename(new_name) to update name
- Persist updated bookshelf to repository
- Publish BookshelfRenamedEvent via domain events
- Return response

RULE-006: New name must be unique within same library (1-255 chars)

Design Pattern: UseCase (Application Layer)
- Orchestrates domain behavior with persistence
- Handles business rule validation (name uniqueness)
- Coordinates event publication
"""

from api.app.modules.bookshelf.application.ports.input import (
    RenameBookshelfRequest,
    RenameBookshelfResponse,
    IRenameBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import BookshelfName


class RenameBookshelfUseCase(IRenameBookshelfUseCase):
    """Implementation of RenameBookshelf UseCase

    Orchestrates:
    1. Load bookshelf from repository
    2. Validate new name (length via ValueObject)
    3. Check uniqueness in same library (RULE-006)
    4. Call domain method: bookshelf.rename(new_name)
    5. Persist updated bookshelf
    6. Return response with new name
    """

    def __init__(self, repository: IBookshelfRepository):
        """
        Initialize RenameBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for persistence
        """
        self.repository = repository

    async def execute(self, request: RenameBookshelfRequest) -> RenameBookshelfResponse:
        """
        Execute bookshelf rename

        Args:
            request: RenameBookshelfRequest with bookshelf_id and new_name

        Returns:
            RenameBookshelfResponse with updated bookshelf data

        Raises:
            ValueError: If bookshelf not found, new name is invalid, or duplicate
            Exception: On unexpected repository errors
        """

        # Step 1: Load bookshelf from repository
        bookshelf = await self.repository.get_by_id(request.bookshelf_id)

        # Step 2: Validate existence
        if not bookshelf:
            raise ValueError(f"Bookshelf {request.bookshelf_id} not found")

        # Step 3: Validate new name format and length (1-255 chars)
        # BookshelfName ValueObject raises ValueError if invalid
        new_bookshelf_name = BookshelfName(request.new_name)

        # Step 4: Check name uniqueness in same library (RULE-006)
        # But exclude current bookshelf's current name from uniqueness check
        if str(bookshelf.name) != request.new_name:
            name_exists = await self.repository.exists_by_name(
                bookshelf.library_id, request.new_name
            )
            if name_exists:
                raise ValueError(
                    f"Bookshelf name '{request.new_name}' already exists in library {bookshelf.library_id}"
                )

        # Step 5: Call domain method to rename
        # This updates name and publishes BookshelfRenamedEvent
        bookshelf.rename(str(new_bookshelf_name))

        # Step 6: Persist updated bookshelf
        await self.repository.save(bookshelf)

        # Step 7: Return response with new name
        return RenameBookshelfResponse.from_domain(bookshelf)
