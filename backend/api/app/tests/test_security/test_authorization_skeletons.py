import pytest
from types import SimpleNamespace
from uuid import UUID, uuid4

from api.app.modules.block.application.ports.input import (
    CreateBlockRequest,
    ListBlocksRequest,
    GetBlockRequest,
)
from api.app.modules.block.application.use_cases.create_block import CreateBlockUseCase
from api.app.modules.block.application.use_cases.list_blocks import ListBlocksUseCase
from api.app.modules.block.application.use_cases.get_block import GetBlockUseCase
from api.app.modules.block.exceptions import BlockForbiddenError

from api.app.modules.tag.application.adapters import _enforce_tag_user_context, DEV_USER_ID
from api.app.modules.tag.exceptions import TagForbiddenError


class FakeBlockRepo:
    def __init__(self, *, block=None):
        self.saved = False
        self._block = block

    async def save(self, block):
        self.saved = True
        return block

    async def get_by_id(self, block_id):
        return self._block

    async def list_paginated(self, *, book_id, page=1, page_size=20, include_deleted=False):
        return [], 0


class FakeBookRepo:
    def __init__(self, *, library_id: UUID):
        self._library_id = library_id

    async def get_by_id(self, book_id: UUID):
        return SimpleNamespace(id=book_id, library_id=self._library_id)


class FakeLibraryRepo:
    def __init__(self, *, owner_user_id: UUID):
        self._owner_user_id = owner_user_id

    async def get_by_id(self, library_id: UUID):
        return SimpleNamespace(id=library_id, user_id=self._owner_user_id)


@pytest.mark.asyncio
async def test_block_create_forbidden_when_not_owner():
    library_id = uuid4()
    owner_user_id = uuid4()
    actor_user_id = uuid4()

    uc = CreateBlockUseCase(
        FakeBlockRepo(),
        book_repository=FakeBookRepo(library_id=library_id),
        library_repository=FakeLibraryRepo(owner_user_id=owner_user_id),
    )

    with pytest.raises(BlockForbiddenError):
        await uc.execute(
            CreateBlockRequest(
                book_id=uuid4(),
                block_type="text",
                content="hello",
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


@pytest.mark.asyncio
async def test_block_list_forbidden_when_not_owner():
    library_id = uuid4()
    owner_user_id = uuid4()
    actor_user_id = uuid4()

    uc = ListBlocksUseCase(
        FakeBlockRepo(),
        book_repository=FakeBookRepo(library_id=library_id),
        library_repository=FakeLibraryRepo(owner_user_id=owner_user_id),
    )

    with pytest.raises(BlockForbiddenError):
        await uc.execute(
            ListBlocksRequest(
                book_id=uuid4(),
                skip=0,
                limit=10,
                include_deleted=False,
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


@pytest.mark.asyncio
async def test_block_get_forbidden_when_not_owner():
    library_id = uuid4()
    owner_user_id = uuid4()
    actor_user_id = uuid4()
    block_id = uuid4()

    fake_block = SimpleNamespace(id=block_id, book_id=uuid4())

    uc = GetBlockUseCase(
        FakeBlockRepo(block=fake_block),
        book_repository=FakeBookRepo(library_id=library_id),
        library_repository=FakeLibraryRepo(owner_user_id=owner_user_id),
    )

    with pytest.raises(BlockForbiddenError):
        await uc.execute(
            GetBlockRequest(
                block_id=block_id,
                actor_user_id=actor_user_id,
                enforce_owner_check=True,
            )
        )


def test_tag_user_context_forbidden_when_actor_not_dev_user():
    actor_user_id = uuid4()
    assert actor_user_id != DEV_USER_ID

    with pytest.raises(TagForbiddenError):
        _enforce_tag_user_context(actor_user_id=actor_user_id, enforce_owner_check=True)
