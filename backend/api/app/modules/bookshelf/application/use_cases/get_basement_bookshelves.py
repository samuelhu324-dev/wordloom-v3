"""
UseCase: GetBasementBookshelves

Purpose:
- Implement the GetBasementBookshelves input port
- List all soft-deleted Bookshelves in a Library with orphaned book counts
- Part of the unified deletion & recovery framework (ADR-038)

Architecture:
- Depends on ILibraryRepository (output port) - validation
- Depends on IBookshelfRepository (output port) - query deleted shelves
- Depends on IBookRepository (output port) - count books per shelf

Related:
- DDD_RULES.yaml: deletion_recovery_framework.basement
- ADR-038: Deletion & Recovery Unified Framework
"""

from uuid import UUID

from api.app.modules.bookshelf.application.ports.input import (
    IGetBasementBookshelvesUseCase,
    GetBasementBookshelvesRequest,
    GetBasementBookshelvesResponse,
    BasementBookshelfItem,
)
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.library.application.ports.output import (
    ILibraryRepository,
    IBookRepository,
)


class GetBasementBookshelvesUseCase(IGetBasementBookshelvesUseCase):
    """
    Use Case: Get all deleted Bookshelves in a Library

    Workflow:
    1. Verify library exists
    2. Query all Bookshelves WHERE library_id=X AND status=DELETED
    3. For each bookshelf, count books in it
    4. Apply pagination
    5. Return BasementBookshelfItem[] with book counts
    """

    def __init__(
        self,
        library_repository: ILibraryRepository,
        bookshelf_repository: IBookshelfRepository,
        book_repository: IBookRepository = None,
    ):
        """
        Initialize GetBasementBookshelvesUseCase

        Args:
            library_repository: For library validation
            bookshelf_repository: For querying deleted bookshelves
            book_repository: For counting books (optional)
        """
        self.library_repository = library_repository
        self.bookshelf_repository = bookshelf_repository
        self.book_repository = book_repository

    async def execute(
        self, request: GetBasementBookshelvesRequest
    ) -> GetBasementBookshelvesResponse:
        """
        Execute get basement bookshelves

        Args:
            request: GetBasementBookshelvesRequest with library_id

        Returns:
            GetBasementBookshelvesResponse with list of deleted shelves
        """
        # Step 1: Verify library exists
        library = await self.library_repository.get_by_id(request.library_id)
        if library is None:
            raise ValueError(f"Library {request.library_id} not found")

        # Step 2: Query deleted bookshelves
        deleted_shelves = await self.bookshelf_repository.find_deleted_by_library(
            library_id=request.library_id,
            limit=request.limit,
            offset=request.offset,
        )

        # Step 3: Build response items with book counts
        items = []
        for bookshelf in deleted_shelves:
            # Count books in this shelf
            book_count = 0
            if self.book_repository:
                try:
                    books = await self.book_repository.find_active_by_bookshelf(
                        bookshelf_id=bookshelf.id
                    )
                    book_count = len(books) if books else 0
                except Exception:
                    book_count = 0

            item = BasementBookshelfItem(
                id=bookshelf.id,
                library_id=bookshelf.library_id,
                name=bookshelf.name.value if hasattr(bookshelf.name, 'value') else str(bookshelf.name),
                orphaned_books_count=book_count,
                status=bookshelf.status.value,
                deleted_at=bookshelf.updated_at.isoformat() if bookshelf.updated_at else "",
            )
            items.append(item)

        # Step 4: Return response
        return GetBasementBookshelvesResponse(
            library_id=request.library_id,
            total_count=len(items),
            bookshelves=items,
            message=f"Found {len(items)} deleted bookshelf(ves) in Basement",
        )
