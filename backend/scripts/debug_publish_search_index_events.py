"""Debug helper: publish Block/Tag events and observe search_index writes.

Why this exists:
- Inserting rows directly into Postgres will NOT trigger the in-process EventBus.
- This script bootstraps the EventBus handlers, publishes a couple events, and
  verifies rows in `search_index` so you can confirm the pipeline end-to-end.

Run (WSL):
  export DATABASE_URL='postgresql://wordloom:wordloom@localhost:5435/wordloom_dev'
  python3 backend/scripts/debug_publish_search_index_events.py

Run (PowerShell):
  $env:DATABASE_URL='postgresql://wordloom:wordloom@localhost:5435/wordloom_dev'
  python backend/scripts/debug_publish_search_index_events.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from api.app.modules.block.domain.events import BlockCreated  # noqa: E402
from api.app.modules.tag.domain.events import TagCreated, TagRenamed  # noqa: E402
from api.app.shared.events import get_event_bus  # noqa: E402

from infra.database.models.search_index_models import SearchIndexModel  # noqa: E402
from infra.database.session import get_session_factory  # noqa: E402
from infra.event_bus.event_handler_registry import EventHandlerRegistry  # noqa: E402


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


async def _fetch_index_row(entity_type: str, entity_id) -> SearchIndexModel | None:
    factory = await get_session_factory()
    async with factory() as session:
        result = await session.execute(
            select(SearchIndexModel).where(
                SearchIndexModel.entity_type == entity_type,
                SearchIndexModel.entity_id == entity_id,
            )
        )
        return result.scalar_one_or_none()


async def main() -> None:
    _configure_logging()

    # Provide a sensible default for local devtest DB.
    os.environ.setdefault(
        "DATABASE_URL", "postgresql://wordloom:wordloom@localhost:5435/wordloom_dev"
    )

    # Import handler package so @EventHandlerRegistry.register decorators run.
    import infra.event_bus.handlers  # noqa: F401

    # Subscribe dispatcher(s) to the global EventBus.
    EventHandlerRegistry.bootstrap()

    bus = get_event_bus()

    block_id = uuid4()
    book_id = uuid4()

    tag_id = uuid4()

    logging.getLogger(__name__).info("Publishing BlockCreated(tagged) → expect INSERT into search_index")
    await bus.publish(
        BlockCreated(
            block_id=block_id,
            book_id=book_id,
            block_type="text",
            content="hello wordloom search index",
            order=1.0,
        )
    )

    logging.getLogger(__name__).info("Publishing TagCreated → expect INSERT into search_index")
    await bus.publish(
        TagCreated(
            tag_id=tag_id,
            name="debug-tag",
            color="#FFFFFF",
            is_toplevel=True,
        )
    )

    logging.getLogger(__name__).info("Publishing TagRenamed → expect UPDATE into search_index")
    await bus.publish(
        TagRenamed(
            tag_id=tag_id,
            old_name="debug-tag",
            new_name="debug-tag-renamed",
        )
    )

    block_row = await _fetch_index_row("block", block_id)
    tag_row = await _fetch_index_row("tag", tag_id)

    if block_row is None:
        raise SystemExit("Expected search_index row for block was not found")
    if tag_row is None:
        raise SystemExit("Expected search_index row for tag was not found")

    logging.getLogger(__name__).info(
        "OK: search_index rows present: block=%s tag=%s", block_row.entity_id, tag_row.entity_id
    )


if __name__ == "__main__":
    asyncio.run(main())
