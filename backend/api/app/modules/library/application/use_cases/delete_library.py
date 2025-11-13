"""DeleteLibrary UseCase - Delete a library

This use case handles:
- Validating library exists
- Soft or hard delete (implementation depends on requirements)
- Handling cascading deletion of related entities

RULE-001: Each user has exactly one library
"""

from uuid import UUID

from ...application.ports.output import LibraryRepository
from ...exceptions import (
    LibraryNotFoundError,
    LibraryOperationError,
)


class DeleteLibraryUseCase:
    """Delete a library"""

    def __init__(self, repository: LibraryRepository):
        self.repository = repository

    async def execute(self, library_id: UUID) -> None:
        """
        Delete library

        Args:
            library_id: Library ID to delete

        Raises:
            LibraryNotFoundError: If library not found
            LibraryOperationError: On persistence error
        """
        library = await self.repository.get_by_id(library_id)
        if not library:
            raise LibraryNotFoundError(library_id)

        try:
            await self.repository.delete(library_id)
        except Exception as e:
            raise LibraryOperationError(f"Failed to delete library: {str(e)}")
