"""
UseCase: ListBasementBooks

Purpose:
- Implement the ListBasementBooks input port
- Query all soft-deleted Books in a Library, grouped by original Bookshelf
- Part of the unified deletion & recovery framework (ADR-038)

Architecture:
- Depends on ILibraryRepository (output port)
- Depends on IBookRepository (output port) for soft-deleted books query
- Depends on IBookshelfRepository (output port) for Bookshelf names

Invariants Enforced:
- BASEMENT-002: Doesn't move data, just queries and groups
- BASEMENT-003: Preserves original bookshelf_id relationships
- Handles orphaned books (missing Bookshelf) gracefully

Related:
- DDD_RULES.yaml: deletion_recovery_framework.basement
- ADR-038: Deletion & Recovery Unified Framework
- Domain: backend/api/app/modules/library/domain/library.py
"""

from datetime import datetime, timezone
from uuid import UUID
from typing import Dict, List

from api.app.modules.library.application.ports.input import (
    IListBasementBooksUseCase,
    ListBasementBooksRequest,
    ListBasementBooksResponse,
    BasementBookItem,
    BasementShelfGroup,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.shared.exceptions import ResourceNotFoundError


class ListBasementBooksUseCase(IListBasementBooksUseCase):
    """
    Use Case: List all soft-deleted Books in a Library (Basement view)

    Workflow:
    1. Verify library exists in repository
    2. Query Books WHERE library_id=X AND soft_deleted_at IS NOT NULL
    3. Group results by original bookshelf_id
    4. For each group, fetch Bookshelf info (name, etc.)
    5. Handle orphaned books (missing Bookshelf) by using placeholder name
    6. Return BasementShelfGroup[] with nested BasementBookItem[]
    7. Apply pagination limits

    Error Handling:
    - ResourceNotFoundError: Library not found in database
    - Gracefully handles missing Bookshelves (orphaned books)

    Pagination:
    - limit: Maximum books per shelf (default 100)
    - offset: Skip first N books (default 0)
    """

    def __init__(
        self,
        library_repository: ILibraryRepository,
        book_repository,  # IBookRepository (not yet defined as interface)
        bookshelf_repository=None,  # IBookshelfRepository (optional)
    ):
        """
        Initialize ListBasementBooksUseCase with dependencies

        Args:
            library_repository: Port for Library persistence
            book_repository: Port for Book persistence (for soft-deleted query)
            bookshelf_repository: Port for Bookshelf info (optional)
        """
        self.library_repository = library_repository
        self.book_repository = book_repository
        self.bookshelf_repository = bookshelf_repository

    async def execute(
        self, request: ListBasementBooksRequest
    ) -> ListBasementBooksResponse:
        """
        Execute the ListBasementBooks use case

        Args:
            request: ListBasementBooksRequest containing library_id and pagination

        Returns:
            ListBasementBooksResponse with grouped deleted books

        Raises:
            ResourceNotFoundError: If library not found
        """
        # Step 1: Verify library exists
        library = await self.library_repository.get_by_id(request.library_id)
        if library is None:
            raise ResourceNotFoundError(
                f"Library {request.library_id} not found",
                resource_type="Library",
                resource_id=str(request.library_id),
            )

        # Step 2: Query soft-deleted books in this library
        deleted_books = await self.book_repository.find_soft_deleted_by_library(
            library_id=request.library_id,
            limit=request.limit,
            offset=request.offset,
        )

        # Step 3: Group books by original bookshelf_id
        shelf_groups_dict: Dict[UUID, List] = {}
        bookshelf_names: Dict[UUID, str] = {}
        total_count = len(deleted_books)

        for book in deleted_books:
            shelf_id = book.bookshelf_id
            if shelf_id not in shelf_groups_dict:
                shelf_groups_dict[shelf_id] = []

            shelf_groups_dict[shelf_id].append(book)

        # Step 4: Fetch Bookshelf names for each group
        for shelf_id in shelf_groups_dict.keys():
            try:
                if self.bookshelf_repository:
                    bookshelf = await self.bookshelf_repository.get_by_id(shelf_id)
                    if bookshelf:
                        bookshelf_names[shelf_id] = bookshelf.get_name_value()
                    else:
                        # Bookshelf doesn't exist (orphaned) - use placeholder
                        bookshelf_names[shelf_id] = f"[Deleted Bookshelf: {shelf_id}]"
                else:
                    # No bookshelf repository provided - use placeholder
                    bookshelf_names[shelf_id] = f"[Unknown Bookshelf: {shelf_id}]"
            except Exception:
                # Gracefully handle any errors fetching bookshelf
                bookshelf_names[shelf_id] = f"[Error loading: {shelf_id}]"

        # Step 5: Build response groups
        shelf_groups: List[BasementShelfGroup] = []
        for shelf_id, books in sorted(shelf_groups_dict.items()):
            shelf_name = bookshelf_names.get(shelf_id, f"[Unknown: {shelf_id}]")

            # Convert books to DTOs
            book_items: List[BasementBookItem] = [
                BasementBookItem(
                    book_id=book.id,
                    title=book.title,
                    bookshelf_id=book.bookshelf_id,
                    bookshelf_name=shelf_name,
                    soft_deleted_at=book.soft_deleted_at,
                )
                for book in books
            ]

            # Create shelf group
            group = BasementShelfGroup(
                bookshelf_id=shelf_id,
                bookshelf_name=shelf_name,
                book_count=len(books),
                books=book_items,
            )
            shelf_groups.append(group)

        # Step 6: Return response
        return ListBasementBooksResponse(
            library_id=request.library_id,
            total_count=total_count,
            shelf_groups=shelf_groups,
            message=f"Found {total_count} deleted book(s) in {len(shelf_groups)} shelf group(s)",
        )
