"""DB environment guard (anti foot-gun).

Goal
- Prevent connecting the API/worker to the wrong database (dev vs test).

Mechanism
- Reads expected environment from WORDLOOM_ENV (recommended: dev|test).
- Validates against a DB-level sentinel row if available.
- Falls back to heuristics based on current_database() if sentinel table is missing.

This is intentionally lightweight and safe to call at startup.
"""

from __future__ import annotations

import os
from typing import Literal, Optional

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession


ExpectedEnv = Literal["dev", "test", "sandbox"]


def _normalize_expected_env(raw: str | None) -> Optional[ExpectedEnv]:
    if not raw:
        return None
    val = raw.strip().lower()
    if val in ("dev", "development"):
        return "dev"
    if val in ("test", "testing"):
        return "test"
    if val in ("sandbox",):
        return "sandbox"
    return None


async def _infer_env_from_db(session: AsyncSession) -> ExpectedEnv:
    db_name = (await session.execute(sa.text("select current_database()"))).scalar_one()
    db_name_str = str(db_name)
    if db_name_str.endswith("_test"):
        return "test"
    if db_name_str.endswith("_dev"):
        return "dev"
    return "sandbox"


async def _read_sentinel_env(session: AsyncSession) -> Optional[ExpectedEnv]:
    try:
        row = (
            await session.execute(
                sa.text("select env from environment_sentinel where id = 1")
            )
        ).scalar_one_or_none()
    except Exception:
        # Most commonly: UndefinedTable. We intentionally treat this as "missing sentinel".
        return None

    if row is None:
        return None

    val = str(row).strip().lower()
    if val in ("dev", "test", "sandbox"):
        return val  # type: ignore[return-value]
    return None


async def assert_expected_database_environment(session: AsyncSession) -> None:
    """Raise RuntimeError if WORDLOOM_ENV doesn't match the connected database."""

    expected = _normalize_expected_env(os.getenv("WORDLOOM_ENV"))
    if expected is None:
        # No explicit expected env configured; do not block startup.
        return

    sentinel_env = await _read_sentinel_env(session)
    inferred_env = await _infer_env_from_db(session)

    actual = sentinel_env or inferred_env

    if actual != expected:
        db_name = (await session.execute(sa.text("select current_database()"))).scalar_one()
        raise RuntimeError(
            "[ENV_GUARD] Refusing to start: database environment mismatch. "
            f"WORDLOOM_ENV={expected!r} actual_db_env={actual!r} db={db_name!r}. "
            "Fix: load the correct .env.dev/.env.test or point DATABASE_URL to the correct DB."
        )


__all__ = ["assert_expected_database_environment"]
