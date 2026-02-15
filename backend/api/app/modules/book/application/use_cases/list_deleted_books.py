"""ListDeletedBooks UseCase - List soft-deleted books from Basement

Implements RULE-012: Basement View Query

This use case handles:
- Querying repository for soft-deleted books (soft_deleted_at IS NOT NULL)
- Supporting optional filtering by bookshelf or library
- Supporting pagination
- Returning paginated list grouped by bookshelf
"""

from typing import List, Optional
from uuid import UUID
import logging

from ...domain import Book
from ..ports.input import ListDeletedBooksRequest
from api.app.modules.book.schemas import BookDetailResponse, BookPaginatedResponse
from ..ports.output import BookRepository
from ...exceptions import (
    BookOperationError,
    BookForbiddenError,
    BookLibraryAssociationError,
    DomainException,
    BookshelfNotFoundError,
)
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from sqlalchemy.ext.asyncio import AsyncSession
from api.app.modules.book.application.tag_summary_loader import load_book_tags_summary
from sqlalchemy import select
from infra.database.models.library_models import LibraryModel

logger = logging.getLogger(__name__)


def _to_iso_string(value):
    if value is None:
        return None
    try:
        if hasattr(value, "isoformat"):
            return value.isoformat()
    except Exception:  # pragma: no cover - 防御性
        return None
    return str(value)


class ListDeletedBooksUseCase:
    """List soft-deleted books from Basement (RULE-012)"""

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

    async def execute(self, request: ListDeletedBooksRequest) -> BookPaginatedResponse:
        """
        List deleted books with optional filtering and pagination

        RULE-012: Basement view - shows all soft-deleted books grouped by bookshelf.

        Args:
            request: ListDeletedBooksRequest containing:
                - bookshelf_id: Optional UUID (filter by original bookshelf)
                - library_id: Optional UUID (permission context)
                - skip: int (pagination offset)
                - limit: int (page size, 1-100)

        Returns:
            BookListResponse with paginated list of soft-deleted books

        Raises:
            BookOperationError: On query error
        """
        try:
            logger.debug(f"ListDeletedBooksUseCase: Querying deleted books, skip={request.skip}, limit={request.limit}")

            await self._enforce_owner_check(request)

            # Query repository for deleted books with filters
            deleted_books, total_count = await self.repository.get_deleted_books(
                skip=request.skip,
                limit=request.limit,
                bookshelf_id=request.bookshelf_id,
                library_id=request.library_id
            )

            logger.debug(f"ListDeletedBooksUseCase: Found {len(deleted_books)} deleted books (total: {total_count})")

            tags_summary_map: dict[UUID, list[str]] = {}
            if self.session:
                try:
                    tags_summary_map = await load_book_tags_summary(
                        self.session,
                        [book.id for book in deleted_books],
                        per_book_limit=self._tags_per_book,
                    )
                except Exception as exc:
                    logger.warning("Failed to load tag summaries for deleted books: %s", exc)

            library_theme_map: dict[UUID, Optional[str]] = {}
            if self.session:
                try:
                    library_ids = {
                        getattr(book, "library_id", None)
                        for book in deleted_books
                        if getattr(book, "library_id", None)
                    }
                    if library_ids:
                        library_theme_map = await self._load_library_theme_colors(library_ids)
                except Exception as exc:
                    logger.warning("Failed to load library colors for deleted books: %s", exc)

            # Convert domain objects to response DTOs
            items: list[BookDetailResponse] = []
            for book in deleted_books:
                title = str(book.title.value) if hasattr(book.title, 'value') else str(book.title)
                has_summary = getattr(book, 'summary', None)
                summary = (
                    str(book.summary.value)
                    if has_summary and getattr(book.summary, 'value', None)
                    else None
                )
                status = book.status.value if hasattr(book.status, 'value') else str(book.status)
                maturity = getattr(book, 'maturity', 'seed') or 'seed'
                if hasattr(maturity, 'value'):
                    maturity = maturity.value

                items.append(
                    BookDetailResponse(
                        id=book.id,
                        library_id=getattr(book, 'library_id', None),
                        bookshelf_id=book.bookshelf_id,
                        title=title,
                        summary=summary,
                        book_type="normal",
                        status=status,
                        maturity=maturity,
                        maturity_score=int(getattr(book, 'maturity_score', 0) or 0),
                        legacy_flag=bool(getattr(book, 'legacy_flag', False)),
                        manual_maturity_override=bool(getattr(book, 'manual_maturity_override', False)),
                        manual_maturity_reason=getattr(book, 'manual_maturity_reason', None),
                        is_pinned=getattr(book, 'is_pinned', False) or False,
                        priority=None,
                        urgency=None,
                        due_at=_to_iso_string(book.due_at),
                        block_count=getattr(book, 'block_count', 0) or 0,
                        cover_icon=getattr(book, 'cover_icon', None),
                        last_visited_at=_to_iso_string(getattr(book, 'last_visited_at', None)),
                        visit_count_90d=int(getattr(book, 'visit_count_90d', 0) or 0),
                        soft_deleted_at=_to_iso_string(book.soft_deleted_at),
                        created_at=_to_iso_string(book.created_at),
                        updated_at=_to_iso_string(book.updated_at),
                        tags_summary=tags_summary_map.get(book.id, []),
                        library_theme_color=library_theme_map.get(getattr(book, 'library_id', None)),
                    )
                )

            page_size = request.limit
            page = (request.skip // page_size) + 1 if page_size else 1
            has_more = request.skip + len(items) < total_count
            return BookPaginatedResponse(
                items=items,
                total=total_count,
                page=page,
                page_size=page_size,
                has_more=has_more,
            )

        except Exception as e:
            if isinstance(e, DomainException):
                raise
            logger.error(f"Failed to list deleted books: {e}", exc_info=True)
            raise BookOperationError(f"Failed to list deleted books: {str(e)}")

    async def _enforce_owner_check(self, request: ListDeletedBooksRequest) -> None:
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
