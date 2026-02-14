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
from api.app.modules.library.exceptions import LibraryNotFoundError, LibraryForbiddenError
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
    - user_id: Deprecated; use list endpoint instead

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
                # Under multi-library, user_id may map to many libraries.
                # Direct single fetch by user_id is deprecated in favor of listing.
                raise ValueError("Query by user_id is deprecated. Use list libraries endpoint.")
        except Exception as e:
            logger.error(f"Repository query failed: {e}", exc_info=True)
            raise

        if not library:
            logger.warning(f"Library not found: library_id={request.library_id}, user_id={request.user_id}")
            raise LibraryNotFoundError(
                f"Library not found (library_id={request.library_id}, user_id={request.user_id})"
            )

        # ================================================================
        # Step 2.5: Authorization (skeleton)
        # ================================================================
        if request.enforce_owner_check and request.actor_user_id is not None:
            if library.user_id != request.actor_user_id:
                raise LibraryForbiddenError(
                    library_id=str(getattr(library, "id", request.library_id)),
                    actor_user_id=str(request.actor_user_id),
                )

        # ================================================================
        # Step 3: Convert to Response DTO
        # ================================================================
        response = GetLibraryResponse(
            library_id=library.id,
            user_id=library.user_id,
            name=library.name.value,
            description=library.description,
            cover_media_id=library.cover_media_id,
            basement_bookshelf_id=library.basement_bookshelf_id,
            created_at=library.created_at,
            updated_at=library.updated_at,
            is_deleted=library.is_deleted(),
            pinned=library.pinned,
            pinned_order=library.pinned_order,
            archived_at=library.archived_at,
            last_activity_at=library.last_activity_at,
            views_count=library.views_count,
            last_viewed_at=library.last_viewed_at,
            theme_color=getattr(library, "theme_color", None),
        )

        logger.info(f"GetLibrary completed successfully: {library.id}")
        return response
