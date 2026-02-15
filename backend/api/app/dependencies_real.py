"""
Real Database Repository Implementation - Production DI Container
使用真实的 SQLAlchemy async Repository

Async Pattern (Nov 17, 2025):
- Library: ✅ AsyncSession + select() + await (完成)
- Bookshelf: ✅ AsyncSession + select() + await (完成)
- Book: ✅ AsyncSession + select() + await (完成)
- Block: ✅ AsyncSession + select() + await + Paperballs recovery (完成)

所有 Repository 都支持完整的异步操作和真实数据库持久化
"""
from sqlalchemy.ext.asyncio import AsyncSession

from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository
from infra.storage.bookshelf_repository_impl import SQLAlchemyBookshelfRepository
from infra.storage.book_repository_impl import SQLAlchemyBookRepository
from infra.storage.block_repository_impl import SQLAlchemyBlockRepository
from infra.storage.media_repository_impl import SQLAlchemyMediaRepository
from infra.storage.basement_repository_impl import SQLAlchemyBasementRepository
from infra.storage.library_tag_association_repository_impl import (
    SQLAlchemyLibraryTagAssociationRepository,
)
from infra.storage.tag_repository_impl import SQLAlchemyTagRepository
from infra.storage.chronicle_repository_impl import SQLAlchemyChronicleRepository
from infra.storage.maturity_repository_impl import SQLAlchemyMaturitySnapshotRepository
from api.app.shared.events import get_event_bus
from api.app.modules.tag.application.adapters import (
    CreateTagAdapter,
    CreateSubtagAdapter,
    UpdateTagAdapter,
    DeleteTagAdapter,
    RestoreTagAdapter,
    AssociateTagAdapter,
    DisassociateTagAdapter,
    SearchTagsAdapter,
    GetMostUsedTagsAdapter,
    ListTagsAdapter,
)
from api.app.modules.chronicle.application.services import (
    ChronicleRecorderService,
    ChronicleQueryService,
)
from api.app.modules.book.domain.services import BookMaturityScoreService
from api.app.modules.maturity.application.adapters import BookAggregateMaturityDataProvider


class DIContainerReal:
    """DI Container with Real Async SQLAlchemy Repositories (Production Mode)"""

    def __init__(self, session: AsyncSession):
        """Initialize with async database session

        Args:
            session: AsyncSession for all database operations
        """
        self.session = session
        self.event_bus = get_event_bus()

        # Initialize all real repositories with async support
        self.library_repo = SQLAlchemyLibraryRepository(session)
        self.bookshelf_repo = SQLAlchemyBookshelfRepository(session)
        self.book_repo = SQLAlchemyBookRepository(session)
        self.block_repo = SQLAlchemyBlockRepository(session)
        self.media_repo = SQLAlchemyMediaRepository(session)
        self.basement_repo = SQLAlchemyBasementRepository(session)
        self.library_tag_repo = SQLAlchemyLibraryTagAssociationRepository(session)
        self.tag_repo = SQLAlchemyTagRepository(session)
        self.chronicle_repo = SQLAlchemyChronicleRepository(session)
        self.maturity_snapshot_repo = SQLAlchemyMaturitySnapshotRepository(session)
        self.book_maturity_score_service = BookMaturityScoreService()
        self.maturity_data_provider = BookAggregateMaturityDataProvider(
            self.book_repo,
            block_repository=self.block_repo,
            tag_repository=self.tag_repo,
        )

    def get_session(self) -> AsyncSession:
        """Expose the active AsyncSession for router helpers."""
        return self.session

    # ========== Library UseCases ==========
    def get_create_library_use_case(self):
        from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase
        return CreateLibraryUseCase(self.library_repo, self.bookshelf_repo, self.event_bus)

    def get_get_library_use_case(self):
        from api.app.modules.library.application.use_cases.get_library import GetLibraryUseCase
        return GetLibraryUseCase(self.library_repo)

    def get_update_library_use_case(self):
        from api.app.modules.library.application.use_cases.update_library import UpdateLibraryUseCase
        return UpdateLibraryUseCase(self.library_repo)

    def get_list_library_tags_use_case(self):
        from api.app.modules.library.application.use_cases.list_library_tags import ListLibraryTagsUseCase
        return ListLibraryTagsUseCase(self.library_tag_repo)

    def get_replace_library_tags_use_case(self):
        from api.app.modules.library.application.use_cases.replace_library_tags import ReplaceLibraryTagsUseCase
        return ReplaceLibraryTagsUseCase(self.library_tag_repo)

    # ========== Media UseCases ==========
    def get_upload_image_use_case(self):
        from api.app.modules.media.application.use_cases.upload_image import UploadImageUseCase
        return UploadImageUseCase(self.media_repo)

    def get_upload_video_use_case(self):
        from api.app.modules.media.application.use_cases.upload_video import UploadVideoUseCase
        return UploadVideoUseCase(self.media_repo)

    def get_delete_media_use_case(self):
        from api.app.modules.media.application.use_cases.delete_media import DeleteMediaUseCase
        return DeleteMediaUseCase(self.media_repo)

    def get_restore_media_use_case(self):
        from api.app.modules.media.application.use_cases.restore_media import RestoreMediaUseCase
        return RestoreMediaUseCase(self.media_repo)

    def get_purge_media_use_case(self):
        from api.app.modules.media.application.use_cases.purge_media import PurgeMediaUseCase
        return PurgeMediaUseCase(self.media_repo)

    def get_associate_media_use_case(self):
        from api.app.modules.media.application.use_cases.associate_media import AssociateMediaUseCase
        return AssociateMediaUseCase(self.media_repo)

    def get_disassociate_media_use_case(self):
        from api.app.modules.media.application.use_cases.disassociate_media import DisassociateMediaUseCase
        return DisassociateMediaUseCase(self.media_repo)

    def get_media_use_case(self):
        from api.app.modules.media.application.use_cases.get_media import GetMediaUseCase
        return GetMediaUseCase(self.media_repo)

    def get_update_media_metadata_use_case(self):
        from api.app.modules.media.application.use_cases.update_media_metadata import (
            UpdateMediaMetadataUseCase,
        )
        return UpdateMediaMetadataUseCase(self.media_repo)

    # ========== Bookshelf UseCases ==========
    def get_create_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.create_bookshelf import CreateBookshelfUseCase
        return CreateBookshelfUseCase(
            self.bookshelf_repo,
            self.tag_repo,
            library_repository=self.library_repo,
        )

    def get_list_bookshelves_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.list_bookshelves import ListBookshelvesUseCase
        return ListBookshelvesUseCase(
            self.bookshelf_repo,
            library_repository=self.library_repo,
        )

    def get_get_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.get_bookshelf import GetBookshelfUseCase
        return GetBookshelfUseCase(
            self.bookshelf_repo,
            library_repository=self.library_repo,
        )

    def get_update_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.update_bookshelf import UpdateBookshelfUseCase
        return UpdateBookshelfUseCase(
            self.bookshelf_repo,
            self.tag_repo,
            library_repository=self.library_repo,
        )

    def get_bookshelf_dashboard_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.get_bookshelf_dashboard import GetBookshelfDashboardUseCase
        return GetBookshelfDashboardUseCase(
            self.session,
            library_repository=self.library_repo,
        )

    def get_delete_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.delete_bookshelf import DeleteBookshelfUseCase
        return DeleteBookshelfUseCase(
            self.bookshelf_repo,
            library_repository=self.library_repo,
        )

    def get_get_basement_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.get_basement import GetBasementUseCase

        return GetBasementUseCase(
            self.bookshelf_repo,
            library_repository=self.library_repo,
        )

    def get_restore_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.restore_bookshelf import RestoreBookshelfUseCase
        return RestoreBookshelfUseCase(self.bookshelf_repo)

    def get_rename_bookshelf_use_case(self):
        from api.app.modules.bookshelf.application.use_cases.rename_bookshelf import RenameBookshelfUseCase
        return RenameBookshelfUseCase(self.bookshelf_repo)

    # ========== Book UseCases ==========
    def get_create_book_use_case(self):
        from api.app.modules.book.application.use_cases.create_book import CreateBookUseCase
        return CreateBookUseCase(
            self.book_repo,
            self.event_bus,
            library_repository=self.library_repo,
        )

    def get_list_books_use_case(self):
        from api.app.modules.book.application.use_cases.list_books import ListBooksUseCase
        return ListBooksUseCase(
            self.book_repo,
            self.session,
            library_repository=self.library_repo,
            bookshelf_repository=self.bookshelf_repo,
        )

    def get_get_book_use_case(self):
        from api.app.modules.book.application.use_cases.get_book import GetBookUseCase
        return GetBookUseCase(
            self.book_repo,
            library_repository=self.library_repo,
        )

    def get_update_book_use_case(self):
        from api.app.modules.book.application.use_cases.update_book import UpdateBookUseCase
        from api.app.modules.book.application.services import BookTagSyncService

        tag_sync_service = BookTagSyncService(
            tag_repository=self.tag_repo,
            associate_use_case=self.get_associate_tag_use_case(),
            disassociate_use_case=self.get_disassociate_tag_use_case(),
        )
        return UpdateBookUseCase(
            self.book_repo,
            self.event_bus,
            tag_sync_service=tag_sync_service,
            library_repository=self.library_repo,
        )

    def get_delete_book_use_case(self):
        from api.app.modules.book.application.services import BookBasementBridge
        from api.app.modules.book.application.use_cases.delete_book import DeleteBookUseCase

        basement_bridge = BookBasementBridge(
            move_book_to_basement_use_case=self.get_move_book_to_basement_use_case(),
            restore_book_from_basement_use_case=self.get_restore_book_from_basement_use_case(),
        )
        return DeleteBookUseCase(
            self.book_repo,
            self.bookshelf_repo,
            self.event_bus,
            basement_bridge=basement_bridge,
            library_repository=self.library_repo,
        )

    def get_move_book_use_case(self):
        from api.app.modules.book.application.use_cases.move_book import MoveBookUseCase
        return MoveBookUseCase(
            self.book_repo,
            self.event_bus,
            bookshelf_repository=self.bookshelf_repo,
            library_repository=self.library_repo,
        )

    def get_restore_book_use_case(self):
        from api.app.modules.book.application.use_cases.restore_book import RestoreBookUseCase
        return RestoreBookUseCase(
            self.book_repo,
            self.event_bus,
            library_repository=self.library_repo,
            bookshelf_repository=self.bookshelf_repo,
        )

    def get_list_deleted_books_use_case(self):
        from api.app.modules.book.application.use_cases.list_deleted_books import ListDeletedBooksUseCase
        return ListDeletedBooksUseCase(
            self.book_repo,
            self.session,
            library_repository=self.library_repo,
            bookshelf_repository=self.bookshelf_repo,
        )

    def get_recalculate_book_maturity_use_case(self):
        from api.app.modules.book.application.use_cases.recalculate_book_maturity import RecalculateBookMaturityUseCase

        return RecalculateBookMaturityUseCase(
            repository=self.book_repo,
            maturity_calculator=self.get_calculate_book_maturity_use_case(),
            event_bus=self.event_bus,
            chronicle_service=self.get_chronicle_recorder_service(),
            snapshot_repository=self.maturity_snapshot_repo,
        )

    def get_update_book_maturity_use_case(self):
        from api.app.modules.book.application.use_cases.update_book_maturity import UpdateBookMaturityUseCase

        return UpdateBookMaturityUseCase(
            repository=self.book_repo,
            score_service=self.book_maturity_score_service,
            event_bus=self.event_bus,
            chronicle_service=self.get_chronicle_recorder_service(),
        )

    # ========== Basement UseCases ==========
    def get_move_book_to_basement_use_case(self):
        from api.app.modules.basement.application.use_cases.move_book_to_basement import (
            MoveBookToBasementUseCase,
        )

        return MoveBookToBasementUseCase(self.book_repo, self.basement_repo)

    def get_restore_book_from_basement_use_case(self):
        from api.app.modules.basement.application.use_cases.restore_book_from_basement import (
            RestoreBookFromBasementUseCase,
        )

        return RestoreBookFromBasementUseCase(self.book_repo, self.basement_repo)

    def get_hard_delete_book_use_case(self):
        from api.app.modules.basement.application.use_cases.hard_delete_book import (
            HardDeleteBookUseCase,
        )

        return HardDeleteBookUseCase(self.book_repo, self.basement_repo)

    def get_list_basement_books_use_case(self):
        from api.app.modules.basement.application.use_cases.list_basement_books import (
            ListBasementBooksUseCase,
        )

        return ListBasementBooksUseCase(self.basement_repo)

    def get_soft_delete_block_use_case(self):
        from api.app.modules.basement.application.use_cases.soft_delete_block import (
            SoftDeleteBlockUseCase,
        )

        return SoftDeleteBlockUseCase(self.block_repo)

    # ========== Maturity UseCases ==========
    def get_calculate_book_maturity_use_case(self):
        from api.app.modules.maturity.application.use_cases import CalculateBookMaturityUseCase

        return CalculateBookMaturityUseCase(
            data_provider=self.maturity_data_provider,
            snapshot_repository=self.maturity_snapshot_repo,
            rule_engine=None,
            transition_policy=None,
        )

    def get_list_maturity_snapshots_use_case(self):
        from api.app.modules.maturity.application.use_cases import ListMaturitySnapshotsUseCase

        return ListMaturitySnapshotsUseCase(self.maturity_snapshot_repo)

    # ========== Block UseCases ==========
    def get_create_block_use_case(self):
        from api.app.modules.block.application.use_cases.create_block import CreateBlockUseCase
        return CreateBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_list_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.list_blocks import ListBlocksUseCase
        return ListBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_get_block_use_case(self):
        from api.app.modules.block.application.use_cases.get_block import GetBlockUseCase
        return GetBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_update_block_use_case(self):
        from api.app.modules.block.application.use_cases.update_block import UpdateBlockUseCase
        return UpdateBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_reorder_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.reorder_blocks import ReorderBlocksUseCase
        return ReorderBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_delete_block_use_case(self):
        from api.app.modules.block.application.use_cases.delete_block import DeleteBlockUseCase
        return DeleteBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_restore_block_use_case(self):
        from api.app.modules.block.application.use_cases.restore_block import RestoreBlockUseCase
        return RestoreBlockUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    def get_list_deleted_blocks_use_case(self):
        from api.app.modules.block.application.use_cases.list_deleted_blocks import ListDeletedBlocksUseCase
        return ListDeletedBlocksUseCase(
            self.block_repo,
            book_repository=self.book_repo,
            library_repository=self.library_repo,
        )

    # ========== Tag UseCases ==========
    def get_create_tag_use_case(self):
        return CreateTagAdapter(self.tag_repo)

    def get_create_subtag_use_case(self):
        return CreateSubtagAdapter(self.tag_repo)

    def get_update_tag_use_case(self):
        return UpdateTagAdapter(self.tag_repo)

    def get_delete_tag_use_case(self):
        return DeleteTagAdapter(self.tag_repo)

    def get_restore_tag_use_case(self):
        return RestoreTagAdapter(self.tag_repo)

    def get_associate_tag_use_case(self):
        return AssociateTagAdapter(
            self.tag_repo,
            library_repository=self.library_repo,
            bookshelf_repository=self.bookshelf_repo,
            book_repository=self.book_repo,
            block_repository=self.block_repo,
            chronicle_service=self.get_chronicle_recorder_service(),
        )

    def get_disassociate_tag_use_case(self):
        return DisassociateTagAdapter(
            self.tag_repo,
            library_repository=self.library_repo,
            bookshelf_repository=self.bookshelf_repo,
            book_repository=self.book_repo,
            block_repository=self.block_repo,
            chronicle_service=self.get_chronicle_recorder_service(),
        )

    def get_search_tags_use_case(self):
        return SearchTagsAdapter(self.tag_repo)

    def get_get_most_used_tags_use_case(self):
        return GetMostUsedTagsAdapter(self.tag_repo)

    def get_list_tags_use_case(self):
        return ListTagsAdapter(self.tag_repo)

    # ========== Chronicle Services ==========
    def get_chronicle_recorder_service(self) -> ChronicleRecorderService:
        return ChronicleRecorderService(self.chronicle_repo)

    def get_chronicle_query_service(self) -> ChronicleQueryService:
        return ChronicleQueryService(self.chronicle_repo)
