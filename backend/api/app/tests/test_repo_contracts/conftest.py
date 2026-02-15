import os
import re

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool


_DEVTEST_DB_5435_SAFE_RE = re.compile(
    r"^postgresql(\+psycopg)?://[^@]+@(?:localhost|127\.0\.0\.1):5435/wordloom_test$",
    re.IGNORECASE,
)


@pytest_asyncio.fixture(autouse=True)
async def _truncate_public_tables_after_each_test() -> None:
    """Strong isolation for repo contract tests.

    Goal: make repo contract tests repeatable across runs (2-3x) without manual cleanup.

    Safety: only runs when DATABASE_URL points to DEVTEST-DB-5435 (localhost:5435/wordloom_test).
    When DATABASE_URL is not set or not safe, this fixture becomes a no-op.
    """

    yield

    url = os.environ.get("DATABASE_URL")
    if not url:
        return

    # Normalize postgres driver variants to the engine we use in tests.
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    if not _DEVTEST_DB_5435_SAFE_RE.match(url):
        return

    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as conn:
            rows = (
                await conn.execute(
                    text(
                        """
                        SELECT tablename
                        FROM pg_tables
                        WHERE schemaname = 'public'
                          AND tablename <> 'alembic_version'
                        """
                    )
                )
            ).all()

            tables = [r[0] for r in rows]
            if not tables:
                return

            table_list = ", ".join([f'"public"."{t}"' for t in tables])
            await conn.execute(text(f"TRUNCATE {table_list} RESTART IDENTITY CASCADE;"))
            await conn.commit()
    finally:
        await engine.dispose()
