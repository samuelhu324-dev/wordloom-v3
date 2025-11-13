"""GetUserLibrary UseCase - Get or create user's library

This use case handles:
- Validating user exists
- Getting existing library or creating if not exists
- RULE-001: Exactly one library per user

Throws LibraryError if inconsistent state detected
"""

from uuid import UUID

from ...domain import Library
from ...application.ports.output import LibraryRepository
from ...exceptions import (
    LibraryNotFoundError,
    LibraryOperationError,
)


class GetUserLibraryUseCase:
    """Get or create user's library (RULE-001: 1 library per user)"""

    def __init__(self, repository: LibraryRepository):
        self.repository = repository

    async def execute(self, user_id: UUID) -> Library:
        """
        Get user's library (creates if needed)

        Args:
            user_id: User ID

        Returns:
            Library domain object

        Raises:
            LibraryOperationError: On persistence error
        """
        try:
            library = await self.repository.get_by_user_id(user_id)
            if library:
                return library

            # Create library if not exists
            new_library = Library.create(user_id=user_id)
            created_library = await self.repository.save(new_library)
            return created_library

        except Exception as e:
            raise LibraryOperationError(f"Failed to get/create user library: {str(e)}")
