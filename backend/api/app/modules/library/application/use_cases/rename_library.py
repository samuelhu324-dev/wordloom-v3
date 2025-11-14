"""
RenameLibrary UseCase

Purpose:
- Rename an existing Library
- Enforce RULE-003: Library name validation (1-255 characters)
- Emit LibraryRenamed event
- Orchestrate Domain → Persistence → EventBus flow

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_5_usecase_splitting
- DDD_RULES.yaml: library.invariants (RULE-003)
- Related events: backend/api/app/modules/library/domain/events.py
"""

from uuid import UUID
import logging

from modules.library.domain.library import Library
from modules.library.domain.library_name import LibraryName
from modules.library.domain.exceptions import LibraryNotFoundError, InvalidLibraryNameError
from modules.library.application.ports.input import (
    RenameLibraryRequest,
    RenameLibraryResponse,
    IRenameLibraryUseCase,
)
from modules.library.application.ports.output import ILibraryRepository

logger = logging.getLogger(__name__)


class RenameLibraryUseCase(IRenameLibraryUseCase):
    """
    UseCase: Rename a Library

    Responsibility:
    - Orchestrate Domain logic with Infrastructure (Repository)
    - NO business logic here - that's Domain's job
    - Just coordinate: Repository.get() → Domain.rename() → Repository.save()

    Business Flow:
    1. [Repository] Retrieve Library by ID
       - If not found → raise LibraryNotFoundError

    2. [Domain] Update name via library.rename()
       - Validates new name (RULE-003) via LibraryName ValueObject
       - Emits LibraryRenamed event
       - Returns updated aggregate

    3. [Repository] Persist changes
       - Translate updated Domain object to ORM model
       - Save to database

    Error Handling:
    - LibraryNotFoundError: Library with given ID doesn't exist
    - InvalidLibraryNameError: Name fails RULE-003 validation (1-255 chars)

    Architecture:
    - Stateless: No internal state, only orchestration
    - Dependency Injection: repository injected via constructor
    - Pure function-like behavior: same inputs → same outputs

    Cross-Module Dependencies:
    - ILibraryRepository (output port): Domain-agnostic interface
    - Library.rename(): Domain method with business logic
    - LibraryName: ValueObject for name validation
    """

    def __init__(self, repository: ILibraryRepository):
        """
        Initialize RenameLibraryUseCase

        Args:
            repository: ILibraryRepository implementation
        """
        self.repository = repository

    async def execute(self, request: RenameLibraryRequest) -> RenameLibraryResponse:
        """
        Execute rename library use case

        Args:
            request: RenameLibraryRequest with library_id and new_name

        Returns:
            RenameLibraryResponse with updated library details

        Raises:
            LibraryNotFoundError: If library doesn't exist
            InvalidLibraryNameError: If name fails validation (RULE-003)
        """
        logger.info(f"RenameLibrary: library_id={request.library_id}, new_name={request.new_name}")

        # Step 1: Retrieve Library from repository
        library: Library = await self.repository.get_by_id(request.library_id)
        if not library:
            logger.error(f"Library not found: {request.library_id}")
            raise LibraryNotFoundError(f"Library {request.library_id} not found")

        # Step 2: Validate name (will raise InvalidLibraryNameError if invalid)
        new_name = LibraryName(request.new_name)

        # Step 3: Update library name in domain
        library.rename(new_name)

        # Step 4: Persist updated library
        await self.repository.save(library)

        logger.info(f"Library renamed successfully: {library.id}")

        # Step 5: Convert domain object to response DTO
        return RenameLibraryResponse.from_domain(library)
