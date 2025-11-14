"""CreateBookshelf UseCase - Create a new Bookshelf in a Library

Responsibilities:
- Validate input (name length, format)
- Check name uniqueness per library (RULE-006)
- Create Bookshelf aggregate using factory method
- Persist to repository
- Return response with created bookshelf data
- Publish BookshelfCreatedEvent

RULE-006: Bookshelf names must be unique per Library (1-255 chars)
RULE-004: Libraries can contain unlimited bookshelves

Design Pattern: UseCase (Application Layer)
- Coordinates between Router, Domain, and Repository
- Handles business logic orchestration
- Manages transactions implicitly via repository
"""

from api.app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    CreateBookshelfResponse,
    ICreateBookshelfUseCase,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import Bookshelf, BookshelfName, BookshelfDescription


class CreateBookshelfUseCase(ICreateBookshelfUseCase):
    """Implementation of CreateBookshelf UseCase

    Orchestrates:
    1. Input validation (name length constraints)
    2. Business rule check (name uniqueness per library)
    3. Factory pattern (Bookshelf.create)
    4. Persistence (repository.save)
    5. Event publication (implicit in domain events)
    6. Response building (DTO serialization)
    """

    def __init__(self, repository: IBookshelfRepository):
        """
        Initialize CreateBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for persistence
        """
        self.repository = repository

    async def execute(self, request: CreateBookshelfRequest) -> CreateBookshelfResponse:
        """
        Execute bookshelf creation

        Args:
            request: CreateBookshelfRequest with library_id, name, optional description

        Returns:
            CreateBookshelfResponse with created bookshelf data

        Raises:
            ValueError: If name is empty, too long, or already exists in library
            BookshelfAlreadyExistsError: If name duplicate detected
            Exception: On unexpected repository errors
        """

        # Step 1: Validate name uniqueness per library (business rule RULE-006)
        name_exists = await self.repository.exists_by_name(
            request.library_id, request.name
        )
        if name_exists:
            raise ValueError(
                f"Bookshelf name '{request.name}' already exists in library {request.library_id}"
            )

        # Step 2: Create BookshelfName ValueObject (validates 1-255 chars)
        bookshelf_name = BookshelfName(request.name)

        # Step 3: Create BookshelfDescription ValueObject if provided
        bookshelf_description = None
        if request.description:
            bookshelf_description = BookshelfDescription(request.description)

        # Step 4: Create Bookshelf aggregate via factory method
        # Factory handles: ID generation, timestamp, status initialization, events
        bookshelf = Bookshelf.create(
            library_id=request.library_id,
            name=str(bookshelf_name),
            description=str(bookshelf_description) if bookshelf_description else None,
        )

        # Step 5: Persist aggregate to repository
        # Repository adapter converts domain object to ORM model, handles IntegrityError
        await self.repository.save(bookshelf)

        # Step 6: Return response DTO
        return CreateBookshelfResponse.from_domain(bookshelf)
