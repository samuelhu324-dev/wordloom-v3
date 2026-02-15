"""ListBooks UseCase - List books in a bookshelf

This use case handles:
- Querying repository for active books (not soft-deleted)
- Supporting pagination
- Returning list of Book domain objects
"""

from typing import List, Tuple, Optional
from uuid import UUID

from ...domain import Book
from ...application.ports.output import BookRepository
from ...application.ports.input import ListBooksRequest
from api.app.modules.book.schemas import BookDetailResponse, BookPaginatedResponse
from ...exceptions import (
    BookOperationError,
    BookForbiddenError,
    BookLibraryAssociationError,
    BookshelfNotFoundError,
    DomainException,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.modules.book.application.tag_summary_loader import load_book_tags_summary
from sqlalchemy import select
from infra.database.models.library_models import LibraryModel
import logging

logger = logging.getLogger(__name__)


class ListBooksUseCase:
    """List books in a bookshelf"""

    def __init__(
        self,
        repository: BookRepository,
        session: Optional[AsyncSession] = None,
        *,
        library_repository: Optional[ILibraryRepository] = None,
        bookshelf_repository: Optional[IBookshelfRepository] = None,
        tags_per_book: int = 3,
    ):
        self.repository = repository
        self.session = session
        self._tags_per_book = tags_per_book
        self.library_repository = library_repository
        self.bookshelf_repository = bookshelf_repository

    async def execute(self, request: ListBooksRequest) -> BookPaginatedResponse:
        """
        List books with pagination

        Args:
            request: ListBooksRequest with:
                - bookshelf_id: Optional filter by bookshelf
                - library_id: Optional filter by library (permission context)
                - include_deleted: Include soft-deleted books (default False)
                - skip: Pagination offset
                - limit: Pagination limit

        Returns:
            BookListResponse with items and total count

        Raises:
            BookOperationError: On query error
        """
        try:
            logger.debug(f"ListBooksUseCase executing: bookshelf_id={request.bookshelf_id}, include_deleted={request.include_deleted}")

            await self._enforce_owner_check(request)

            # Call repository method to fetch books
            if request.bookshelf_id:
                books, total = await self.repository.get_by_bookshelf_id(
                    request.bookshelf_id,
                    request.skip,
                    request.limit,
                    include_deleted=request.include_deleted
                )
            else:
                # If no bookshelf specified, list all books for the library (if provided)
                books, total = await self.repository.get_by_library_id(
                    request.library_id,
                    request.skip,
                    request.limit,
                    include_deleted=request.include_deleted
                ) if request.library_id else ([], 0)

            logger.debug(f"ListBooksUseCase found {len(books)} books (total: {total})")

            tags_summary_map: dict[UUID, list[str]] = {}
            if self.session:
                try:
                    tags_summary_map = await load_book_tags_summary(
                        self.session,
                        [book.id for book in books],
                        per_book_limit=self._tags_per_book,
                    )
                except Exception as exc:
                    logger.warning("Failed to load tag summaries for books: %s", exc)

            library_theme_map: dict[UUID, Optional[str]] = {}
            if self.session:
                try:
                    library_ids = {
                        getattr(book, "library_id", None)
                        for book in books
                        if getattr(book, "library_id", None)
                    }
                    if library_ids:
                        library_theme_map = await self._load_library_theme_colors(library_ids)
                except Exception as exc:
                    logger.warning("Failed to load library colors for books: %s", exc)

            # Convert to response format with proper handling of Value Objects and Enums
            items: list[BookDetailResponse] = []
            for book in books:
                try:
                    # Handle title (Value Object with .value or plain string)
                    title = str(book.title) if book.title else ''

                    # Handle summary (Value Object or None)
                    summary = None
                    if book.summary:
                        if hasattr(book.summary, 'value'):
                            summary = str(book.summary.value) if book.summary.value else None
                        else:
                            summary = str(book.summary) if book.summary else None

                    # Handle status (Enum with .value or plain string)
                    status = ''
                    if book.status:
                        if hasattr(book.status, 'value'):
                            status = book.status.value
                        else:
                            status = str(book.status)

                    maturity = getattr(book, 'maturity', 'seed') or 'seed'
                    if hasattr(maturity, 'value'):
                        maturity = maturity.value
                    else:
                        maturity = str(maturity) if maturity else 'seed'

                    # Handle datetime fields - ensure proper isoformat conversion
                    def to_iso_string(dt_value):
                        """Convert datetime to ISO string or None"""
                        if dt_value is None:
                            return None
                        try:
                            if hasattr(dt_value, 'isoformat'):
                                return dt_value.isoformat()
                            else:
                                return str(dt_value)
                        except Exception as e:
                            logger.warning(f"Failed to convert datetime {dt_value}: {e}")
                            return None

                    created_at = to_iso_string(getattr(book, 'created_at', None))
                    updated_at = to_iso_string(getattr(book, 'updated_at', None))
                    soft_deleted_at = to_iso_string(getattr(book, 'soft_deleted_at', None))
                    due_at = to_iso_string(getattr(book, 'due_at', None))

                    maturity_score = int(getattr(book, "maturity_score", 0) or 0)
                    legacy_flag = bool(getattr(book, "legacy_flag", False))
                    manual_override = bool(getattr(book, "manual_maturity_override", False))
                    manual_override_reason = getattr(book, "manual_maturity_reason", None)
                    last_visited_at = to_iso_string(getattr(book, 'last_visited_at', None))
                    visit_count_90d = int(getattr(book, 'visit_count_90d', 0) or 0)

                    response_item = BookDetailResponse(
                        id=book.id,
                        library_id=getattr(book, 'library_id', None),
                        bookshelf_id=book.bookshelf_id,
                        title=title,
                        summary=summary,
                        book_type="normal",  # 未来可扩展
                        status=status or "draft",
                        maturity=maturity,
                        maturity_score=maturity_score,
                        legacy_flag=legacy_flag,
                        manual_maturity_override=manual_override,
                        manual_maturity_reason=manual_override_reason,
                        is_pinned=getattr(book, 'is_pinned', False) or False,
                        priority=None,
                        urgency=None,
                        due_at=due_at,
                        block_count=getattr(book, 'block_count', 0) or 0,
                        cover_icon=getattr(book, 'cover_icon', None),
                        cover_media_id=getattr(book, 'cover_media_id', None),
                        last_visited_at=last_visited_at,
                        visit_count_90d=visit_count_90d,
                        soft_deleted_at=soft_deleted_at,
                        created_at=created_at,
                        updated_at=updated_at,
                        tags_summary=tags_summary_map.get(book.id, []),
                        library_theme_color=library_theme_map.get(getattr(book, "library_id", None)),
                    )
                    items.append(response_item)
                except Exception as e:
                    logger.error(f"Failed to convert book {getattr(book, 'id', 'unknown')}: {e}", exc_info=True)
                    raise BookOperationError(f"Failed to serialize book data: {str(e)}")

            page_size = request.limit
            page = (request.skip // page_size) + 1 if page_size else 1
            has_more = request.skip + len(items) < total
            return BookPaginatedResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                has_more=has_more,
            )
        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"ListBooksUseCase failed: {e}", exc_info=True)
            raise BookOperationError(f"Failed to list books: {str(e)}")

    async def _enforce_owner_check(self, request: ListBooksRequest) -> None:
        if not getattr(request, "enforce_owner_check", True) or getattr(request, "actor_user_id", None) is None:
            return
        if self.library_repository is None:
            raise BookOperationError("library_repository is required when enforcing owner checks")

        library_id = getattr(request, "library_id", None)
        if library_id is None and getattr(request, "bookshelf_id", None) is not None:
            if self.bookshelf_repository is None:
                raise BookOperationError("bookshelf_repository is required to resolve library_id from bookshelf_id")
            shelf = await self.bookshelf_repository.get_by_id(request.bookshelf_id)
            if not shelf:
                raise BookshelfNotFoundError(bookshelf_id=str(request.bookshelf_id))
            library_id = getattr(shelf, "library_id", None)

        if library_id is None:
            # Keep existing behavior: without context we return empty results.
            return

        library = await self.library_repository.get_by_id(library_id)
        if not library:
            raise BookLibraryAssociationError(library_id=str(library_id), reason="Library not found")
        if getattr(library, "user_id", None) != request.actor_user_id:
            raise BookForbiddenError(
                library_id=str(library_id),
                actor_user_id=str(request.actor_user_id),
                reason="Actor does not own this library",
            )

    async def _load_library_theme_colors(self, library_ids: set[UUID]) -> dict[UUID, Optional[str]]:
        if not self.session or not library_ids:
            return {}
        stmt = select(LibraryModel.id, LibraryModel.theme_color).where(LibraryModel.id.in_(list(library_ids)))
        result = await self.session.execute(stmt)
        rows = result.all()
        return {row[0]: row[1] for row in rows}
