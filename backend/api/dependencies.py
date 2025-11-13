"""
Dependency Injection (DI) Container

管理应用的所有依赖注入。包括：
- 数据库会话工厂
- Repository 实例
- UseCase 实例
- EventBus 实例

这是应用的中枢，所有依赖从这里获取。
"""

from typing import Optional
from sqlalchemy.orm import Session, sessionmaker
from uuid import UUID

# Infrastructure
from app.infra.event_bus import EventBus, get_event_bus

# Modules - Repositories (Output Ports)
from app.modules.tag.application.ports.output import ITagRepository
from app.modules.media.application.ports.output import IMediaRepository
from app.modules.library.application.ports.output import ILibraryRepository
from app.modules.bookshelf.application.ports.output import IBookshelfRepository
from app.modules.book.application.ports.output import IBookRepository
from app.modules.block.application.ports.output import IBlockRepository

# Modules - Repository Implementations
from app.infra.storage import (
    SQLAlchemyTagRepository,
    SQLAlchemyMediaRepository,
    SQLAlchemyLibraryRepository,
    SQLAlchemyBookshelfRepository,
    SQLAlchemyBookRepository,
    SQLAlchemyBlockRepository,
)

# Modules - Tag UseCases (Input Ports)
from app.modules.tag.application.use_cases import (
    CreateTagUseCase,
    CreateSubtagUseCase,
    UpdateTagUseCase,
    DeleteTagUseCase,
    RestoreTagUseCase,
    AssociateTagUseCase,
    DisassociateTagUseCase,
    SearchTagsUseCase,
    GetMostUsedTagsUseCase,
)

# Modules - Media UseCases
from app.modules.media.application.use_cases import (
    UploadImageUseCase,
    UploadVideoUseCase,
    UpdateMediaMetadataUseCase,
    DeleteMediaUseCase,
    RestoreMediaUseCase,
    PurgeMediaUseCase,
    AssociateMediaUseCase,
    DisassociateMediaUseCase,
    GetMediaUseCase,
)

# Modules - Library UseCases
from app.modules.library.application.use_cases import (
    GetUserLibraryUseCase,
    DeleteLibraryUseCase,
)

# Modules - Bookshelf UseCases
from app.modules.bookshelf.application.use_cases import (
    CreateBookshelfUseCase,
    ListBookshelvesUseCase,
    GetBookshelfUseCase,
    UpdateBookshelfUseCase,
    DeleteBookshelfUseCase,
    GetBasementUseCase,
)

# Modules - Book UseCases
from app.modules.book.application.use_cases import (
    CreateBookUseCase,
    ListBooksUseCase,
    GetBookUseCase,
    UpdateBookUseCase,
    DeleteBookUseCase,
    RestoreBookUseCase,
    ListDeletedBooksUseCase,
)

# Modules - Block UseCases
from app.modules.block.application.use_cases import (
    CreateBlockUseCase,
    ListBlocksUseCase,
    GetBlockUseCase,
    UpdateBlockUseCase,
    ReorderBlocksUseCase,
    DeleteBlockUseCase,
    RestoreBlockUseCase,
    ListDeletedBlocksUseCase,
)


class DIContainer:
    """
    依赖注入容器

    管理应用的所有依赖实例的创建和生命周期。
    支持单例和请求作用域的依赖。

    Example:
        di = DIContainer(SessionLocal)
        use_case = di.get_create_tag_use_case()
        response = await use_case.execute(request)
    """

    def __init__(self, session_factory: Optional[sessionmaker] = None):
        """
        初始化 DI 容器

        Args:
            session_factory: SQLAlchemy SessionLocal 工厂函数
        """
        self.session_factory = session_factory
        self.event_bus = get_event_bus()

        # 缓存的单例实例（如果需要）
        self._repositories_cache = {}

    # ========================================================================
    # Database Session Provider
    # ========================================================================

    def get_session(self) -> Session:
        """
        获取数据库会话

        Returns:
            SQLAlchemy Session 实例
        """
        if self.session_factory is None:
            raise RuntimeError("SessionLocal factory not configured")
        return self.session_factory()

    # ========================================================================
    # Repository Factories (Output Ports)
    # ========================================================================

    def get_tag_repository(self) -> ITagRepository:
        """获取 Tag Repository"""
        session = self.get_session()
        return SQLAlchemyTagRepository(session)

    def get_media_repository(self) -> IMediaRepository:
        """获取 Media Repository"""
        session = self.get_session()
        return SQLAlchemyMediaRepository(session)

    def get_library_repository(self) -> ILibraryRepository:
        """获取 Library Repository"""
        session = self.get_session()
        return SQLAlchemyLibraryRepository(session)

    def get_bookshelf_repository(self) -> IBookshelfRepository:
        """获取 Bookshelf Repository"""
        session = self.get_session()
        return SQLAlchemyBookshelfRepository(session)

    def get_book_repository(self) -> IBookRepository:
        """获取 Book Repository"""
        session = self.get_session()
        return SQLAlchemyBookRepository(session)

    def get_block_repository(self) -> IBlockRepository:
        """获取 Block Repository"""
        session = self.get_session()
        return SQLAlchemyBlockRepository(session)

    # ========================================================================
    # Tag UseCase Factories
    # ========================================================================

    def get_create_tag_use_case(self) -> CreateTagUseCase:
        """获取 CreateTagUseCase"""
        repo = self.get_tag_repository()
        return CreateTagUseCase(repo, self.event_bus)

    def get_create_subtag_use_case(self) -> CreateSubtagUseCase:
        """获取 CreateSubtagUseCase"""
        repo = self.get_tag_repository()
        return CreateSubtagUseCase(repo, self.event_bus)

    def get_update_tag_use_case(self) -> UpdateTagUseCase:
        """获取 UpdateTagUseCase"""
        repo = self.get_tag_repository()
        return UpdateTagUseCase(repo, self.event_bus)

    def get_delete_tag_use_case(self) -> DeleteTagUseCase:
        """获取 DeleteTagUseCase"""
        repo = self.get_tag_repository()
        return DeleteTagUseCase(repo, self.event_bus)

    def get_restore_tag_use_case(self) -> RestoreTagUseCase:
        """获取 RestoreTagUseCase"""
        repo = self.get_tag_repository()
        return RestoreTagUseCase(repo, self.event_bus)

    def get_associate_tag_use_case(self) -> AssociateTagUseCase:
        """获取 AssociateTagUseCase"""
        repo = self.get_tag_repository()
        return AssociateTagUseCase(repo, self.event_bus)

    def get_disassociate_tag_use_case(self) -> DisassociateTagUseCase:
        """获取 DisassociateTagUseCase"""
        repo = self.get_tag_repository()
        return DisassociateTagUseCase(repo, self.event_bus)

    def get_search_tags_use_case(self) -> SearchTagsUseCase:
        """获取 SearchTagsUseCase"""
        repo = self.get_tag_repository()
        return SearchTagsUseCase(repo, self.event_bus)

    def get_get_most_used_tags_use_case(self) -> GetMostUsedTagsUseCase:
        """获取 GetMostUsedTagsUseCase"""
        repo = self.get_tag_repository()
        return GetMostUsedTagsUseCase(repo, self.event_bus)

    # ========================================================================
    # Media UseCase Factories
    # ========================================================================

    def get_upload_image_use_case(self) -> UploadImageUseCase:
        """获取 UploadImageUseCase"""
        repo = self.get_media_repository()
        return UploadImageUseCase(repo, self.event_bus)

    def get_upload_video_use_case(self) -> UploadVideoUseCase:
        """获取 UploadVideoUseCase"""
        repo = self.get_media_repository()
        return UploadVideoUseCase(repo, self.event_bus)

    def get_update_media_metadata_use_case(self) -> UpdateMediaMetadataUseCase:
        """获取 UpdateMediaMetadataUseCase"""
        repo = self.get_media_repository()
        return UpdateMediaMetadataUseCase(repo, self.event_bus)

    def get_delete_media_use_case(self) -> DeleteMediaUseCase:
        """获取 DeleteMediaUseCase"""
        repo = self.get_media_repository()
        return DeleteMediaUseCase(repo, self.event_bus)

    def get_restore_media_use_case(self) -> RestoreMediaUseCase:
        """获取 RestoreMediaUseCase"""
        repo = self.get_media_repository()
        return RestoreMediaUseCase(repo, self.event_bus)

    def get_purge_media_use_case(self) -> PurgeMediaUseCase:
        """获取 PurgeMediaUseCase"""
        repo = self.get_media_repository()
        return PurgeMediaUseCase(repo, self.event_bus)

    def get_associate_media_use_case(self) -> AssociateMediaUseCase:
        """获取 AssociateMediaUseCase"""
        repo = self.get_media_repository()
        return AssociateMediaUseCase(repo, self.event_bus)

    def get_disassociate_media_use_case(self) -> DisassociateMediaUseCase:
        """获取 DisassociateMediaUseCase"""
        repo = self.get_media_repository()
        return DisassociateMediaUseCase(repo, self.event_bus)

    def get_get_media_use_case(self) -> GetMediaUseCase:
        """获取 GetMediaUseCase"""
        repo = self.get_media_repository()
        return GetMediaUseCase(repo, self.event_bus)

    # ========================================================================
    # Library UseCase Factories
    # ========================================================================

    def get_get_user_library_use_case(self) -> GetUserLibraryUseCase:
        """获取 GetUserLibraryUseCase"""
        repo = self.get_library_repository()
        return GetUserLibraryUseCase(repo, self.event_bus)

    def get_delete_library_use_case(self) -> DeleteLibraryUseCase:
        """获取 DeleteLibraryUseCase"""
        repo = self.get_library_repository()
        return DeleteLibraryUseCase(repo, self.event_bus)

    # ========================================================================
    # Bookshelf UseCase Factories
    # ========================================================================

    def get_create_bookshelf_use_case(self) -> CreateBookshelfUseCase:
        """获取 CreateBookshelfUseCase"""
        repo = self.get_bookshelf_repository()
        return CreateBookshelfUseCase(repo, self.event_bus)

    def get_list_bookshelves_use_case(self) -> ListBookshelvesUseCase:
        """获取 ListBookshelvesUseCase"""
        repo = self.get_bookshelf_repository()
        return ListBookshelvesUseCase(repo, self.event_bus)

    def get_get_bookshelf_use_case(self) -> GetBookshelfUseCase:
        """获取 GetBookshelfUseCase"""
        repo = self.get_bookshelf_repository()
        return GetBookshelfUseCase(repo, self.event_bus)

    def get_update_bookshelf_use_case(self) -> UpdateBookshelfUseCase:
        """获取 UpdateBookshelfUseCase"""
        repo = self.get_bookshelf_repository()
        return UpdateBookshelfUseCase(repo, self.event_bus)

    def get_delete_bookshelf_use_case(self) -> DeleteBookshelfUseCase:
        """获取 DeleteBookshelfUseCase"""
        repo = self.get_bookshelf_repository()
        return DeleteBookshelfUseCase(repo, self.event_bus)

    def get_get_basement_use_case(self) -> GetBasementUseCase:
        """获取 GetBasementUseCase"""
        repo = self.get_bookshelf_repository()
        return GetBasementUseCase(repo, self.event_bus)

    # ========================================================================
    # Book UseCase Factories
    # ========================================================================

    def get_create_book_use_case(self) -> CreateBookUseCase:
        """获取 CreateBookUseCase"""
        repo = self.get_book_repository()
        return CreateBookUseCase(repo, self.event_bus)

    def get_list_books_use_case(self) -> ListBooksUseCase:
        """获取 ListBooksUseCase"""
        repo = self.get_book_repository()
        return ListBooksUseCase(repo, self.event_bus)

    def get_get_book_use_case(self) -> GetBookUseCase:
        """获取 GetBookUseCase"""
        repo = self.get_book_repository()
        return GetBookUseCase(repo, self.event_bus)

    def get_update_book_use_case(self) -> UpdateBookUseCase:
        """获取 UpdateBookUseCase"""
        repo = self.get_book_repository()
        return UpdateBookUseCase(repo, self.event_bus)

    def get_delete_book_use_case(self) -> DeleteBookUseCase:
        """获取 DeleteBookUseCase"""
        repo = self.get_book_repository()
        return DeleteBookUseCase(repo, self.event_bus)

    def get_restore_book_use_case(self) -> RestoreBookUseCase:
        """获取 RestoreBookUseCase"""
        repo = self.get_book_repository()
        return RestoreBookUseCase(repo, self.event_bus)

    def get_list_deleted_books_use_case(self) -> ListDeletedBooksUseCase:
        """获取 ListDeletedBooksUseCase"""
        repo = self.get_book_repository()
        return ListDeletedBooksUseCase(repo, self.event_bus)

    # ========================================================================
    # Block UseCase Factories
    # ========================================================================

    def get_create_block_use_case(self) -> CreateBlockUseCase:
        """获取 CreateBlockUseCase"""
        repo = self.get_block_repository()
        return CreateBlockUseCase(repo, self.event_bus)

    def get_list_blocks_use_case(self) -> ListBlocksUseCase:
        """获取 ListBlocksUseCase"""
        repo = self.get_block_repository()
        return ListBlocksUseCase(repo, self.event_bus)

    def get_get_block_use_case(self) -> GetBlockUseCase:
        """获取 GetBlockUseCase"""
        repo = self.get_block_repository()
        return GetBlockUseCase(repo, self.event_bus)

    def get_update_block_use_case(self) -> UpdateBlockUseCase:
        """获取 UpdateBlockUseCase"""
        repo = self.get_block_repository()
        return UpdateBlockUseCase(repo, self.event_bus)

    def get_reorder_blocks_use_case(self) -> ReorderBlocksUseCase:
        """获取 ReorderBlocksUseCase"""
        repo = self.get_block_repository()
        return ReorderBlocksUseCase(repo, self.event_bus)

    def get_delete_block_use_case(self) -> DeleteBlockUseCase:
        """获取 DeleteBlockUseCase"""
        repo = self.get_block_repository()
        return DeleteBlockUseCase(repo, self.event_bus)

    def get_restore_block_use_case(self) -> RestoreBlockUseCase:
        """获取 RestoreBlockUseCase"""
        repo = self.get_block_repository()
        return RestoreBlockUseCase(repo, self.event_bus)

    def get_list_deleted_blocks_use_case(self) -> ListDeletedBlocksUseCase:
        """获取 ListDeletedBlocksUseCase"""
        repo = self.get_block_repository()
        return ListDeletedBlocksUseCase(repo, self.event_bus)


# 全局 DI 容器实例
_di_container: Optional[DIContainer] = None


def get_di_container_provider(session_factory: Optional[sessionmaker] = None) -> DIContainer:
    """
    获取 DI 容器实例

    支持在 FastAPI 中作为依赖注入使用。

    Args:
        session_factory: SQLAlchemy SessionLocal（可选）

    Returns:
        DIContainer 实例

    Example:
        app.dependency_overrides[get_di_container_provider] = lambda: DIContainer(SessionLocal)
    """
    global _di_container
    if _di_container is None:
        _di_container = DIContainer(session_factory)
    return _di_container


def reset_di_container() -> None:
    """重置 DI 容器（用于测试）"""
    global _di_container
    _di_container = None


__all__ = [
    "DIContainer",
    "get_di_container_provider",
    "reset_di_container",
]
