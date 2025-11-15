"""
CreateLibrary UseCase

Purpose:
- Create a new Library for a user
- Enforce RULE-001: Each user has exactly one Library
- Enforce RULE-003: Library name validation
- Emit LibraryCreated and BasementCreated events
- Orchestrate Domain → Persistence → EventBus flow

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_5_usecase_splitting (Line ~600-650)
- DDD_RULES.yaml: library.invariants (RULE-001, RULE-003)
- Related events: backend/api/app/modules/library/domain/events.py
"""

from uuid import UUID
import logging

from api.app.modules.library.domain import Library
from api.app.modules.library.exceptions import LibraryAlreadyExistsError
from api.app.modules.library.application.ports.input import (
    CreateLibraryRequest,
    CreateLibraryResponse,
    ICreateLibraryUseCase,
)
from api.app.modules.library.application.ports.output import ILibraryRepository

logger = logging.getLogger(__name__)


class CreateLibraryUseCase(ICreateLibraryUseCase):
    """
    UseCase: Create a new Library

    Responsibility:
    - Orchestrate Domain logic with Infrastructure (Repository)
    - NO business logic here - that's Domain's job
    - Just coordinate: Domain.create() → Repository.save() → EventBus.publish()

    Business Flow:
    1. [Domain] Create Library aggregate via Library.create()
       - Validates name (RULE-003) via LibraryName ValueObject
       - Generates unique IDs (library_id, basement_id)
       - Emits LibraryCreated + BasementCreated events

    2. [Repository] Persist to database
       - Translate Domain object to ORM model
       - Enforce unique constraint on user_id (RULE-001)
       - Catch IntegrityError and convert to LibraryAlreadyExistsError

    3. [EventBus] Publish events
       - Listeners will create Basement bookshelf
       - Listeners will initialize Chronicle session
       - Listeners will update UI

    Failure Cases:
    - LibraryAlreadyExistsError: User already has a library (RULE-001 violation)
    - ValueError: Name is invalid (RULE-003 violation)
    - DatabaseError: Database connection issues

    Cross-Reference:
    - Domain: backend/api/app/modules/library/domain/library.py
    - Repository: backend/infra/storage/library_repository_impl.py
    - Events: backend/api/app/modules/library/domain/events.py
    """

    def __init__(
        self,
        repository: ILibraryRepository,
        event_bus,  # IEventBus from backend/infra/event_bus.py
    ):
        """
        Initialize CreateLibrary UseCase with dependencies

        Args:
            repository: ILibraryRepository implementation (from DI container)
            event_bus: EventBus instance for publishing domain events
        """
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse:
        """
        Execute CreateLibrary business operation

        Args:
            request: CreateLibraryRequest with user_id and name

        Returns:
            CreateLibraryResponse with created library details

        Raises:
            LibraryAlreadyExistsError: If user already has a library
            ValueError: If name is invalid
            Exception: For other infrastructure errors

        Step-by-Step Execution:
        1. Validate request parameters (basic checks)
        2. Call Domain factory: Library.create(user_id, name)
        3. Persist via Repository
        4. Publish domain events to EventBus
        5. Return response DTO

        Transaction Handling:
        - Service caller (or FastAPI middleware) handles session commit/rollback
        - If any step fails, entire transaction rolls back
        - Events are only published AFTER successful persistence
        """
        logger.info(f"CreateLibrary starting for user {request.user_id}")

        # ================================================================
        # Step 1: [DOMAIN] Create Library aggregate
        # ================================================================
        try:
            # Domain factory method - encapsulates all creation logic
            library = Library.create(
                user_id=request.user_id,
                name=request.name,
            )
            logger.debug(f"Library aggregate created: {library.id}")
        except ValueError as e:
            # Name validation failed (RULE-003)
            logger.warning(f"Library creation failed - invalid name: {e}")
            raise

        # ================================================================
        # Step 2: [REPOSITORY] Persist to database
        # ================================================================
        try:
            await self.repository.save(library)
            logger.info(f"Library persisted to database: {library.id}")
        except LibraryAlreadyExistsError as e:
            # User already has a library (RULE-001 violation detected at DB level)
            logger.warning(f"Library creation failed - user already has library: {e}")
            raise
        except Exception as e:
            # Other database errors
            logger.error(f"Library persistence failed: {e}", exc_info=True)
            raise

        # ================================================================
        # Step 3: [EVENTBUS] Publish domain events
        # ================================================================
        try:
            for event in library.events:
                await self.event_bus.publish(event)
                logger.debug(f"Event published: {event.__class__.__name__}")
            logger.info(f"All events published for library {library.id}")
        except Exception as e:
            # Event publishing failed - still considered failure
            logger.error(f"Event publishing failed: {e}", exc_info=True)
            raise

        # ================================================================
        # Step 4: [RESPONSE] Convert to DTO and return
        # ================================================================
        response = CreateLibraryResponse(
            library_id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            basement_bookshelf_id=library.basement_bookshelf_id,
            created_at=library.created_at,
        )

        logger.info(f"CreateLibrary completed successfully for user {request.user_id}")
        return response
