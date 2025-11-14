"""GetBookshelf UseCase - Retrieve a Bookshelf by ID

Responsibilities:
- Query bookshelf from repository by ID
- Handle not-found case (raise exception or return empty)
- Return response DTO with bookshelf data

Design Pattern: UseCase (Application Layer)
- Read-only operation (Query)
- No state changes, no events published
- Simple pass-through from repository to Router
"""

from api.app.modules.bookshelf.application.ports.input import (
    GetBookshelfRequest,
    GetBookshelfResponse,
    IGetBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository


class GetBookshelfUseCase(IGetBookshelfUseCase):
    """Implementation of GetBookshelf UseCase

    Orchestrates:
    1. Query repository by ID
    2. Validate result (not None)
    3. Convert domain object to response DTO
    """

    def __init__(self, repository: IBookshelfRepository):
        """
        Initialize GetBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for queries
        """
        self.repository = repository

    async def execute(self, request: GetBookshelfRequest) -> GetBookshelfResponse:
        """
        Execute bookshelf retrieval

        Args:
            request: GetBookshelfRequest with bookshelf_id

        Returns:
            GetBookshelfResponse with bookshelf data

        Raises:
            ValueError: If bookshelf not found
            Exception: On unexpected repository errors
        """

        # Step 1: Query repository by ID
        bookshelf = await self.repository.get_by_id(request.bookshelf_id)

        # Step 2: Validate existence
        if not bookshelf:
            raise ValueError(f"Bookshelf {request.bookshelf_id} not found")

        # Step 3: Convert to response DTO and return
        return GetBookshelfResponse.from_domain(bookshelf)
