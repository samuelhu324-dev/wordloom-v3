"""
GetLibrary UseCase

Purpose:
- Retrieve a Library by ID or by User ID
- Enforce RULE-001 uniqueness when querying by user_id
- Handle not found cases gracefully

Cross-Reference:
- HEXAGONAL_RULES.yaml: step_5_usecase_splitting (Line ~600-650)
- DDD_RULES.yaml: library.invariants (RULE-001)
"""

from uuid import UUID
import logging

from api.app.modules.library.domain import Library
from api.app.modules.library.exceptions import LibraryNotFoundError
from api.app.modules.library.application.ports.input import (
    GetLibraryRequest,
    GetLibraryResponse,
    IGetLibraryUseCase,
)
from api.app.modules.library.application.ports.output import ILibraryRepository

logger = logging.getLogger(__name__)


class GetLibraryUseCase(IGetLibraryUseCase):
    """
    UseCase: Retrieve a Library

    Can retrieve by:
    - library_id: Direct lookup
    - user_id: Unique lookup (RULE-001: exactly one per user)

    Failure Cases:
    - Library not found (404)
    - Invalid request (both or neither of library_id/user_id provided)
    """

    def __init__(self, repository: ILibraryRepository):
        """Initialize with Repository dependency"""
        self.repository = repository

    async def execute(self, request: GetLibraryRequest) -> GetLibraryResponse:
        """
        Execute GetLibrary business operation

        Args:
            request: GetLibraryRequest with either library_id or user_id

        Returns:
            GetLibraryResponse with library details

        Raises:
            LibraryNotFoundError: If library not found
            ValueError: If request parameters are invalid
        """
        logger.info(f"GetLibrary starting: library_id={request.library_id}, user_id={request.user_id}")

        # ================================================================
        # Step 1: Validate request parameters
        # ================================================================
        has_library_id = request.library_id is not None
        has_user_id = request.user_id is not None

        if has_library_id and has_user_id:
            raise ValueError("Cannot provide both library_id and user_id")

        if not has_library_id and not has_user_id:
            raise ValueError("Must provide either library_id or user_id")

        # ================================================================
        # Step 2: Query Repository
        # ================================================================
        try:
            if request.library_id:
                logger.debug(f"Querying by library_id: {request.library_id}")
                library = await self.repository.get_by_id(request.library_id)
            else:
                logger.debug(f"Querying by user_id: {request.user_id}")
                library = await self.repository.get_by_user_id(request.user_id)
        except Exception as e:
            logger.error(f"Repository query failed: {e}", exc_info=True)
            raise

        if not library:
            logger.warning(f"Library not found: library_id={request.library_id}, user_id={request.user_id}")
            raise LibraryNotFoundError(
                f"Library not found (library_id={request.library_id}, user_id={request.user_id})"
            )

        # ================================================================
        # Step 3: Convert to Response DTO
        # ================================================================
        response = GetLibraryResponse(
            library_id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            basement_bookshelf_id=library.basement_bookshelf_id,
            created_at=library.created_at,
            updated_at=library.updated_at,
            is_deleted=library.is_deleted(),
        )

        logger.info(f"GetLibrary completed successfully: {library.id}")
        return response
