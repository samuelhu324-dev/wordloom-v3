"""CreateBookshelf UseCase - Create a new Bookshelf in a Library

Responsibilities:
- Validate input (name length, format)
- Check name uniqueness per library (RULE-006)
- Create Bookshelf aggregate using factory method
- Persist to repository
- Associate initial tags when provided
- Return DTO including tag summary
- Publish BookshelfCreatedEvent

RULE-006: Bookshelf names must be unique per Library (1-255 chars)
RULE-004: Libraries can contain unlimited bookshelves

Design Pattern: UseCase (Application Layer)
- Coordinates between Router, Domain, and Repository
- Handles business logic orchestration
- Manages transactions implicitly via repository
"""

from typing import List, Optional, Tuple
from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    CreateBookshelfRequest,
    CreateBookshelfResponse,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.bookshelf.domain import Bookshelf
from api.app.modules.bookshelf.exceptions import (
    BookshelfAlreadyExistsError,
    BookshelfForbiddenError,
    BookshelfLibraryAssociationError,
    BookshelfOperationError,
    BookshelfTagSyncError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.tag.application.ports.output import TagRepository
from api.app.modules.tag.domain import EntityType
from api.app.modules.tag.exceptions import TagNotFoundError, TagOperationError


class CreateBookshelfUseCase:
    """Implementation of CreateBookshelf UseCase

    Orchestrates:
    1. Input validation (name length constraints)
    2. Business rule check (name uniqueness per library)
    3. Factory pattern (Bookshelf.create)
    4. Persistence (repository.save)
    5. Initial tag association (optional)
    6. Event publication (implicit in domain events)
    7. Returns response DTO for transport layer
    """

    def __init__(
        self,
        repository: IBookshelfRepository,
        tag_repository: Optional[TagRepository] = None,
        *,
        library_repository: Optional[ILibraryRepository] = None,
    ):
        """
        Initialize CreateBookshelfUseCase

        Args:
            repository: IBookshelfRepository implementation for persistence
        """
        self.repository = repository
        self.tag_repository = tag_repository
        self.library_repository = library_repository

    async def execute(self, request: CreateBookshelfRequest) -> CreateBookshelfResponse:
        """
        Execute bookshelf creation

        Args:
            request: CreateBookshelfRequest with library_id, name, optional description

        Returns:
            CreateBookshelfResponse DTO with bookshelf and tag data

        Raises:
            ValueError: If name is empty, too long, or already exists in library
            BookshelfAlreadyExistsError: If name duplicate detected
            Exception: On unexpected repository errors
        """

        await self._enforce_library_owner(request)

        # Step 1: Validate name uniqueness per library (business rule RULE-006)
        name_exists = await self.repository.exists_by_name(
            request.library_id, request.name
        )
        if name_exists:
            raise BookshelfAlreadyExistsError(
                library_id=str(request.library_id),
                name=request.name,
            )

        # Step 2: Create Bookshelf aggregate via factory method
        # Factory handles: ID generation, timestamp, status initialization, events
        # Factory will also create BookshelfName and BookshelfDescription ValueObjects
        bookshelf = Bookshelf.create(
            library_id=request.library_id,
            name=request.name,  # Pass raw string; factory will create ValueObject
            description=request.description,  # Pass raw string or None; factory will handle
        )

        # Step 3: Persist aggregate to repository
        # Repository adapter converts domain object to ORM model, handles IntegrityError
        await self.repository.save(bookshelf)

        # Step 4: Associate initial tags when provided
        tag_ids, tag_names = await self._apply_initial_tags(bookshelf, request.tag_ids)

        # Step 5: Return response DTO for transport layer
        return CreateBookshelfResponse.from_domain(
            bookshelf,
            tag_ids=tag_ids,
            tags_summary=tag_names,
        )

    async def _enforce_library_owner(self, request: CreateBookshelfRequest) -> None:
        if not request.enforce_owner_check or request.actor_user_id is None:
            return
        if self.library_repository is None:
            raise BookshelfOperationError(
                bookshelf_id="<unknown>",
                operation="authorize",
                reason="library_repository is required when enforcing owner checks",
            )

        library = await self.library_repository.get_by_id(request.library_id)
        if not library:
            raise BookshelfLibraryAssociationError(
                bookshelf_id="<unknown>",
                library_id=str(request.library_id),
                reason="Library not found",
            )
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookshelfForbiddenError(
                library_id=str(request.library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )

    async def _apply_initial_tags(
        self,
        bookshelf: Bookshelf,
        incoming_tag_ids: Optional[List[UUID]],
    ) -> Tuple[List[UUID], List[str]]:
        """Associate provided tag IDs with the newly created bookshelf"""

        if not incoming_tag_ids or not self.tag_repository:
            return [], []

        ordered_unique: List[UUID] = []
        seen: set[UUID] = set()
        for tag_id in incoming_tag_ids:
            if tag_id in seen:
                continue
            ordered_unique.append(tag_id)
            seen.add(tag_id)

        try:
            for tag_id in ordered_unique:
                await self.tag_repository.associate_tag_with_entity(
                    tag_id,
                    EntityType.BOOKSHELF,
                    bookshelf.id,
                )
        except (TagNotFoundError, TagOperationError) as exc:
            raise BookshelfTagSyncError(
                bookshelf_id=str(bookshelf.id),
                reason=str(exc),
            ) from exc

        final_tags = await self.tag_repository.find_by_entity(
            EntityType.BOOKSHELF,
            bookshelf.id,
        )
        lookup = {tag.id: tag.name for tag in final_tags}
        final_ids = [tag_id for tag_id in ordered_unique if tag_id in lookup]
        final_names = [lookup[tag_id] for tag_id in final_ids]
        return final_ids, final_names

