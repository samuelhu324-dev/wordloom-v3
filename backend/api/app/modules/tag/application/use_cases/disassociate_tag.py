"""DisassociateTag UseCase - Remove tag association from an entity

This use case handles:
- Validating tag exists
- Deleting TagAssociation record
- Decrementing tag.usage_count
- Idempotent: disassociating non-existent association is no-op
- Persisting via repository
"""

from uuid import UUID

from ...domain import EntityType
from ...application.ports.output import TagRepository
from api.app.modules.library.application.ports.output import ILibraryRepository
from api.app.modules.bookshelf.application.ports.output import IBookshelfRepository
from api.app.modules.book.application.ports.output import BookRepository
from api.app.modules.block.application.ports.output import BlockRepository
from ...exceptions import (
    TagNotFoundError,
    TagOperationError,
    TagForbiddenError,
)


class DisassociateTagUseCase:
    """Remove association between a tag and an entity"""

    def __init__(
        self,
        repository: TagRepository,
        *,
        library_repository: ILibraryRepository,
        bookshelf_repository: IBookshelfRepository,
        book_repository: BookRepository,
        block_repository: BlockRepository,
    ):
        self.repository = repository
        self.library_repository = library_repository
        self.bookshelf_repository = bookshelf_repository
        self.book_repository = book_repository
        self.block_repository = block_repository

    async def _resolve_library_id(self, entity_type: EntityType, entity_id: UUID) -> UUID:
        if entity_type == EntityType.LIBRARY:
            return entity_id
        if entity_type == EntityType.BOOKSHELF:
            bookshelf = await self.bookshelf_repository.get_by_id(entity_id)
            if not bookshelf:
                raise TagOperationError("Target bookshelf not found")
            return bookshelf.library_id
        if entity_type == EntityType.BOOK:
            book = await self.book_repository.get_by_id(entity_id)
            if not book:
                raise TagOperationError("Target book not found")
            return book.library_id
        if entity_type == EntityType.BLOCK:
            block = await self.block_repository.get_by_id(entity_id)
            if not block:
                raise TagOperationError("Target block not found")
            book = await self.book_repository.get_by_id(block.book_id)
            if not book:
                raise TagOperationError("Target book not found")
            return book.library_id

        raise TagOperationError(f"Unsupported entity_type: {entity_type}")

    async def execute(
        self,
        tag_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
        *,
        actor_user_id: UUID | None = None,
        enforce_owner_check: bool = True,
    ) -> None:
        """
        Execute disassociate tag use case

        Args:
            tag_id: ID of tag to disassociate
            entity_type: Type of entity (Book, Bookshelf, Block)
            entity_id: ID of entity

        Raises:
            TagNotFoundError: If tag not found
            TagOperationError: On persistence error
        """
        tag = await self.repository.get_by_id(tag_id)
        if not tag:
            raise TagNotFoundError(tag_id)

        if enforce_owner_check and actor_user_id is not None:
            library_id = await self._resolve_library_id(entity_type, entity_id)
            library = await self.library_repository.get_by_id(library_id)
            if not library:
                raise TagOperationError("Target library not found")
            if library.user_id != actor_user_id:
                raise TagForbiddenError(
                    "Forbidden: entity does not belong to actor",
                    actor_user_id=str(actor_user_id),
                    entity_type=str(entity_type.value),
                    entity_id=str(entity_id),
                )

        try:
            await self.repository.disassociate_tag_from_entity(
                tag_id,
                entity_type,
                entity_id
            )
        except Exception as e:
            raise TagOperationError(f"Failed to disassociate tag: {str(e)}")
