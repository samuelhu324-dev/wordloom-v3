import datetime as dt

import pytest

from uuid import uuid4

from sqlalchemy import text

from infra.storage.search_repository_impl import PostgresSearchAdapter
from infra.search.fake_elastic_candidate_provider import FakeElasticCandidateProvider
from api.app.modules.search.application.ports.candidate_provider import Candidate
from infra.database.models.search_index_models import SearchIndexModel
from infra.database.models.library_models import LibraryModel
from infra.database.models.bookshelf_models import BookshelfModel
from infra.database.models.book_models import BookModel
from infra.database.models.block_models import BlockModel
from infra.database.models.tag_models import TagModel, TagAssociationModel, EntityType


@pytest.mark.asyncio
async def test_two_stage_block_search_returns_tags_and_applies_filters(db_session):
    user_id = uuid4()

    library_id = uuid4()
    bookshelf_id = uuid4()

    book_id = uuid4()
    other_book_id = uuid4()

    block_id = uuid4()
    other_book_block_id = uuid4()
    soft_deleted_block_id = uuid4()

    tag_a_id = uuid4()
    tag_b_id = uuid4()
    deleted_tag_id = uuid4()

    now = dt.datetime.now(dt.timezone.utc)

    library = LibraryModel(id=library_id, user_id=user_id, name="L")
    shelf = BookshelfModel(id=bookshelf_id, library_id=library_id, name="S")

    book = BookModel(id=book_id, bookshelf_id=bookshelf_id, library_id=library_id, title="B")
    other_book = BookModel(
        id=other_book_id,
        bookshelf_id=bookshelf_id,
        library_id=library_id,
        title="B2",
    )

    block = BlockModel(
        id=block_id,
        book_id=book_id,
        type="paragraph",
        content="quantum entanglement",
        order=0,
    )
    other_book_block = BlockModel(
        id=other_book_block_id,
        book_id=other_book_id,
        type="paragraph",
        content="quantum other book",
        order=1,
    )
    soft_deleted_block = BlockModel(
        id=soft_deleted_block_id,
        book_id=book_id,
        type="paragraph",
        content="quantum deleted",
        order=2,
        soft_deleted_at=now,
    )

    tag_a = TagModel(id=tag_a_id, user_id=user_id, name="tag-a")
    tag_b = TagModel(id=tag_b_id, user_id=user_id, name="tag-b")
    deleted_tag = TagModel(id=deleted_tag_id, user_id=user_id, name="tag-deleted", deleted_at=now)

    assoc_a = TagAssociationModel(tag_id=tag_a_id, entity_type=EntityType.BLOCK, entity_id=block_id)
    assoc_b = TagAssociationModel(tag_id=tag_b_id, entity_type=EntityType.BLOCK, entity_id=block_id)
    assoc_deleted = TagAssociationModel(tag_id=deleted_tag_id, entity_type=EntityType.BLOCK, entity_id=block_id)

    # Ensure our inserted candidates are included even when the devtest DB already
    # contains many search_index rows ordered by event_version.
    max_event_version = (
        await db_session.execute(
            text("SELECT COALESCE(MAX(event_version), 0) FROM search_index")
        )
    ).scalar_one()
    base_event_version = int(max_event_version) + 1000

    si_block = SearchIndexModel(
        entity_type="block",
        entity_id=block_id,
        text="quantum entanglement",
        snippet="snippet-1",
        event_version=base_event_version,
    )
    si_other_book_block = SearchIndexModel(
        entity_type="block",
        entity_id=other_book_block_id,
        text="quantum other book",
        snippet="snippet-2",
        event_version=base_event_version + 1,
    )
    si_deleted_block = SearchIndexModel(
        entity_type="block",
        entity_id=soft_deleted_block_id,
        text="quantum deleted",
        snippet="snippet-3",
        event_version=base_event_version + 2,
    )

    # Flush in dependency order to avoid FK ordering surprises.
    db_session.add(library)
    await db_session.flush()

    db_session.add(shelf)
    await db_session.flush()

    db_session.add_all([book, other_book])
    await db_session.flush()

    db_session.add_all([block, other_book_block, soft_deleted_block])
    await db_session.flush()

    db_session.add_all([tag_a, tag_b, deleted_tag])
    await db_session.flush()

    db_session.add_all([assoc_a, assoc_b, assoc_deleted])
    await db_session.flush()

    db_session.add_all([si_block, si_other_book_block, si_deleted_block])
    await db_session.flush()

    repo = PostgresSearchAdapter(db_session)

    # Sanity: our test data should be visible and match FTS.
    fts_count = (
        await db_session.execute(
            text(
                """
                SELECT count(*)
                FROM search_index
                WHERE entity_type = 'block'
                  AND entity_id = :block_id
                  AND to_tsvector('english', text) @@ plainto_tsquery('english', :q)
                """
            ),
            {"q": "quantum", "block_id": block_id},
        )
    ).scalar_one()
    assert fts_count >= 1

    # book_id filter should exclude the other book block.
    # soft_deleted filter should exclude the soft-deleted block.
    hits = await repo.search_block_hits_two_stage(
        q="quantum",
        book_id=book_id,
        limit=20,
        candidate_limit=200,
    )

    assert [h.id for h in hits] == [block_id]
    assert hits[0].snippet == "snippet-1"
    assert sorted(hits[0].tags) == ["tag-a", "tag-b"]


@pytest.mark.asyncio
async def test_two_stage_block_search_can_swap_stage1_provider_only(db_session):
    user_id = uuid4()

    library_id = uuid4()
    bookshelf_id = uuid4()

    book_id = uuid4()
    other_book_id = uuid4()

    block_id = uuid4()
    other_book_block_id = uuid4()
    soft_deleted_block_id = uuid4()

    tag_a_id = uuid4()
    tag_b_id = uuid4()

    now = dt.datetime.now(dt.timezone.utc)

    library = LibraryModel(id=library_id, user_id=user_id, name="L")
    shelf = BookshelfModel(id=bookshelf_id, library_id=library_id, name="S")

    book = BookModel(id=book_id, bookshelf_id=bookshelf_id, library_id=library_id, title="B")
    other_book = BookModel(
        id=other_book_id,
        bookshelf_id=bookshelf_id,
        library_id=library_id,
        title="B2",
    )

    block = BlockModel(
        id=block_id,
        book_id=book_id,
        type="paragraph",
        content="alpha content",
        order=0,
    )
    other_book_block = BlockModel(
        id=other_book_block_id,
        book_id=other_book_id,
        type="paragraph",
        content="beta content",
        order=1,
    )
    soft_deleted_block = BlockModel(
        id=soft_deleted_block_id,
        book_id=book_id,
        type="paragraph",
        content="gamma deleted",
        order=2,
        soft_deleted_at=now,
    )

    tag_a = TagModel(id=tag_a_id, user_id=user_id, name="tag-a")
    tag_b = TagModel(id=tag_b_id, user_id=user_id, name="tag-b")

    assoc_a = TagAssociationModel(tag_id=tag_a_id, entity_type=EntityType.BLOCK, entity_id=block_id)
    assoc_b = TagAssociationModel(tag_id=tag_b_id, entity_type=EntityType.BLOCK, entity_id=block_id)

    # Flush in dependency order to avoid FK ordering surprises.
    db_session.add(library)
    await db_session.flush()

    db_session.add(shelf)
    await db_session.flush()

    db_session.add_all([book, other_book])
    await db_session.flush()

    db_session.add_all([block, other_book_block, soft_deleted_block])
    await db_session.flush()

    db_session.add_all([tag_a, tag_b])
    await db_session.flush()

    db_session.add_all([assoc_a, assoc_b])
    await db_session.flush()

    # Stage1 is now a swappable provider. Simulate Elastic recall returning extra candidates.
    fake_provider = FakeElasticCandidateProvider(
        candidates=[
            Candidate(entity_id=soft_deleted_block_id, order_key=30, snippet=""),
            Candidate(entity_id=other_book_block_id, order_key=20, snippet="fake-2"),
            Candidate(entity_id=block_id, order_key=10, snippet="fake-1"),
        ]
    )

    repo = PostgresSearchAdapter(db_session)
    hits = await repo.search_block_hits_two_stage(
        q="ignored-by-fake",
        book_id=book_id,
        limit=20,
        candidate_limit=200,
        candidate_provider=fake_provider,
    )

    # Stage2 filters should still apply.
    assert [h.id for h in hits] == [block_id]
    assert hits[0].snippet == "fake-1"
    assert sorted(hits[0].tags) == ["tag-a", "tag-b"]
