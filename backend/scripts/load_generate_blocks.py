"""Load generator: create/update/delete blocks via API.

Goal
- Generate controllable streams of /api/v1/blocks operations (create/update/delete) to produce outbox events.
- Intended for observing produced/processed/lag metrics.

Usage (WSL2 / bash)

    export API_BASE='http://localhost:30011'
    export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'

    # Optional knobs
    export TOTAL_BLOCKS=1000  # total operations (back-compat name)
    # or: export TOTAL_OPS=1000
    export RATE_PER_SEC=50
    export CONCURRENCY=10
    export BLOCK_TYPE=text
    export CONTENT_BYTES=200

    # Scenario knobs (default: create)
    # export LOADGEN_SCENARIO=create_then_update
    # export POOL_SIZE=500
    # export HOTSET_SIZE=50

    python3 scripts/load_generate_blocks.py

You can also set BOOK_ID to skip DB discovery:

    export BOOK_ID='<uuid>'

Notes
- Reads a book_id from DB if BOOK_ID is not set.
- Writes blocks through API (so domain + events/outbox are exercised).
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict
from uuid import UUID

import httpx
from sqlalchemy import select

# Ensure backend root is on sys.path so `infra.*` imports work whether this
# script is run from the repo root (python backend/scripts/...) or from
# backend/ directly (python scripts/...).
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

@dataclass(frozen=True)
class _Stats:
    ok: int
    failed: int


def _short(text: str, max_len: int = 160) -> str:
    text = (text or "").replace("\n", " ").replace("\r", " ").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _classify_failure(
    *,
    status_code: int | None,
    body: Any | None,
    text: str | None,
    exc: Exception | None,
) -> str:
    """Build a compact, stable failure key for grouping and summary printing."""
    if exc is not None:
        return f"EXC_{type(exc).__name__}"

    sc = status_code or 0
    key = f"HTTP_{sc}"

    code: str | None = None
    message: str | None = None

    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, dict):
            code = detail.get("code")
            message = detail.get("message") or detail.get("error") or detail.get("reason")
        elif isinstance(detail, str) and detail:
            message = detail

        message = message or body.get("message") or body.get("error")

    if code:
        key += f" {code}"
    if message:
        key += f" {_short(str(message), 90)}"
    elif text:
        key += f" {_short(text, 90)}"

    return key.strip()


def _get_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def _get_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return float(raw)


def _get_bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_str_env(name: str, default: str) -> str:
    raw = os.getenv(name)
    return default if raw is None or raw == "" else raw


def _clamp_int(value: int, *, min_value: int, max_value: int) -> int:
    return max(min_value, min(max_value, value))


async def _pick_book_id(database_url: str) -> UUID:
    # Delay imports so we don't trigger infra.database.session fallback/printing
    # unless we actually need DB discovery.
    os.environ["DATABASE_URL"] = database_url

    from infra.database.models.book_models import BookModel
    from infra.database.session import get_session_factory

    session_factory = await get_session_factory()
    async with session_factory() as session:
        book_id = (
            await session.execute(
                select(BookModel.id)
                .where(BookModel.soft_deleted_at.is_(None))
                .order_by(BookModel.updated_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    if book_id is None:
        raise RuntimeError(
            "No active books found in DB. Set BOOK_ID explicitly or create a book in wordloom_test."
        )
    return book_id


async def _create_block(
    *,
    client: httpx.AsyncClient,
    api_base: str,
    book_id: UUID,
    block_type: str,
    content: str,
    metadata: dict[str, Any],
) -> UUID:
    payload: dict[str, Any] = {
        "book_id": str(book_id),
        "block_type": block_type,
        "content": content,
        "metadata": metadata,
    }
    resp = await client.post(f"{api_base}/api/v1/blocks", json=payload)
    resp.raise_for_status()
    body = resp.json()
    block_id = body.get("id") if isinstance(body, dict) else None
    if not block_id:
        raise RuntimeError(f"Create block response missing id: {body!r}")
    return UUID(str(block_id))


async def _update_block(
    *,
    client: httpx.AsyncClient,
    api_base: str,
    block_id: UUID,
    content: str | None,
    metadata: dict[str, Any] | None,
) -> None:
    # NOTE: Current API contract requires block_id in body (UpdateBlockRequest.block_id)
    # even though it's also present in the path.
    payload: dict[str, Any] = {"block_id": str(block_id)}
    if content is not None:
        payload["content"] = content
    if metadata is not None:
        payload["metadata"] = metadata
    resp = await client.patch(f"{api_base}/api/v1/blocks/{block_id}", json=payload)
    resp.raise_for_status()


async def _delete_block(
    *,
    client: httpx.AsyncClient,
    api_base: str,
    block_id: UUID,
) -> None:
    resp = await client.delete(f"{api_base}/api/v1/blocks/{block_id}")
    # Treat 404 as idempotent success (already deleted).
    if resp.status_code not in (204, 404):
        resp.raise_for_status()


def _make_content(seq: int, size: int) -> str:
    # Deterministic content helps when debugging search/indexing.
    base = f"loadgen block seq={seq} "
    if size <= len(base):
        return base
    return base + ("x" * (size - len(base)))


async def main() -> None:
    api_base = os.getenv("API_BASE", "http://localhost:30001").rstrip("/")
    database_url = os.getenv("DATABASE_URL")
    explicit_book_id = os.getenv("BOOK_ID")
    allow_non_test_db = os.getenv("LOADGEN_ALLOW_NON_TEST_DB") in ("1", "true", "True")

    scenario = _get_str_env("LOADGEN_SCENARIO", "create").strip().lower()
    if scenario not in {"create", "create_then_update", "create_then_delete", "mixed"}:
        raise RuntimeError(
            "Invalid LOADGEN_SCENARIO. Expected one of: create, create_then_update, create_then_delete, mixed"
        )

    total_ops = _get_int_env("TOTAL_OPS", _get_int_env("TOTAL_BLOCKS", 1000))
    rate_per_sec = _get_float_env("RATE_PER_SEC", 50.0)
    concurrency = _get_int_env("CONCURRENCY", 10)

    block_type = os.getenv("BLOCK_TYPE", "text")
    content_bytes = _get_int_env("CONTENT_BYTES", 200)

    request_timeout_s = _get_float_env("REQUEST_TIMEOUT_S", 60.0)

    pool_size = _get_int_env("POOL_SIZE", 0)
    if pool_size <= 0:
        pool_size = min(500, max(1, total_ops // 5))

    hotset_size = _get_int_env("HOTSET_SIZE", 0)
    if hotset_size <= 0:
        hotset_size = max(1, pool_size // 10)
    hotset_size = _clamp_int(hotset_size, min_value=1, max_value=pool_size)

    create_ratio = _get_float_env("MIX_CREATE_RATIO", 0.6)
    update_ratio = _get_float_env("MIX_UPDATE_RATIO", 0.3)
    delete_ratio = _get_float_env("MIX_DELETE_RATIO", 0.1)
    normalize_ratios = _get_bool_env("MIX_NORMALIZE", True)
    ratio_sum = create_ratio + update_ratio + delete_ratio
    if ratio_sum <= 0:
        raise RuntimeError("Invalid mix ratios: sum must be > 0")
    if normalize_ratios:
        create_ratio /= ratio_sum
        update_ratio /= ratio_sum
        delete_ratio /= ratio_sum

    fail_summary_top_n = _get_int_env("FAIL_SUMMARY_TOP_N", 8)
    fail_summary_samples = _get_int_env("FAIL_SUMMARY_SAMPLES", 3)
    fail_summary_every = _get_int_env("FAIL_SUMMARY_EVERY", 50)
    fail_line_compact = os.getenv("FAIL_LINE_COMPACT", "1") in ("1", "true", "True")

    fail_counts: Counter[str] = Counter()
    fail_samples: DefaultDict[str, list[str]] = defaultdict(list)
    fail_total = 0

    def record_failure(reason_key: str, sample: str) -> None:
        nonlocal fail_total
        fail_total += 1
        fail_counts[reason_key] += 1
        if len(fail_samples[reason_key]) < fail_summary_samples:
            fail_samples[reason_key].append(_short(sample, 240))

    def print_fail_summary(header: str) -> None:
        if not fail_counts:
            return
        top = fail_counts.most_common(fail_summary_top_n)
        print(f"\n[{header}] total_failed={fail_total} unique_reasons={len(fail_counts)} top={len(top)}")
        for reason, cnt in top:
            print(f"  - {cnt}x  {reason}")
            for s in fail_samples.get(reason, []):
                print(f"      sample: {s}")
        print("")

    if total_ops <= 0:
        raise RuntimeError("TOTAL_OPS/TOTAL_BLOCKS must be > 0")
    if rate_per_sec <= 0:
        raise RuntimeError("RATE_PER_SEC must be > 0")
    if concurrency <= 0:
        raise RuntimeError("CONCURRENCY must be > 0")

    if explicit_book_id:
        book_id = UUID(explicit_book_id)
    else:
        if not database_url:
            raise RuntimeError(
                "Missing DATABASE_URL (used to auto-pick a book_id from wordloom_test).\n"
                "Fix (WSL2 / bash):\n"
                "  export DATABASE_URL='postgresql+psycopg://wordloom:wordloom@localhost:5435/wordloom_test'\n"
                "  # or set BOOK_ID explicitly: export BOOK_ID='<uuid>'\n"
                "Note: use ASCII quotes '...' (not the Chinese/typographic quote ’…’)."
            )

        if ("wordloom_test" not in database_url) and (not allow_non_test_db):
            raise RuntimeError(
                "Refusing to run: DATABASE_URL does not look like wordloom_test.\n"
                f"DATABASE_URL={database_url!r}\n"
                "Set DATABASE_URL to the test DB, or set LOADGEN_ALLOW_NON_TEST_DB=1 to override."
            )
        book_id = await _pick_book_id(database_url)

    interval = 1.0 / rate_per_sec

    print(
        f"load_generate_blocks: scenario={scenario} api={api_base} book_id={book_id} total_ops={total_ops} "
        f"rate={rate_per_sec}/s concurrency={concurrency} type={block_type} content_bytes={content_bytes} "
        f"pool_size={pool_size} hotset_size={hotset_size}"
    )

    sem = asyncio.Semaphore(concurrency)
    stats_ok = 0
    stats_failed = 0

    pool_lock = asyncio.Lock()
    block_pool: list[UUID] = []

    async def _record_http_failure(seq: int, *, resp: httpx.Response) -> None:
        nonlocal stats_failed
        stats_failed += 1
        try:
            body = resp.json()
        except Exception:
            body = None

        reason_key = _classify_failure(
            status_code=resp.status_code,
            body=body,
            text=getattr(resp, "text", None),
            exc=None,
        )
        sample = (
            f"status={resp.status_code} "
            f"body={body if body is not None else _short(getattr(resp, 'text', ''), 200)}"
        )
        record_failure(reason_key, sample)

        if fail_line_compact:
            print(f"FAILED seq={seq} reason={reason_key}")

        if fail_summary_every > 0 and (fail_total % fail_summary_every == 0):
            print_fail_summary(header=f"fail_summary@{fail_total}")


    async def _one_create(seq: int, client: httpx.AsyncClient) -> None:
        nonlocal stats_ok, stats_failed
        async with sem:
            try:
                created_id = await _create_block(
                    client=client,
                    api_base=api_base,
                    book_id=book_id,
                    block_type=block_type,
                    content=_make_content(seq, content_bytes),
                    metadata={"loadgen": True, "seq": seq, "op": "create"},
                )
                async with pool_lock:
                    block_pool.append(created_id)
                stats_ok += 1
            except httpx.HTTPStatusError as exc:
                await _record_http_failure(seq, resp=exc.response)
            except Exception as exc:  # noqa: BLE001
                stats_failed += 1
                reason_key = _classify_failure(status_code=None, body=None, text=None, exc=exc)
                record_failure(reason_key, f"{type(exc).__name__}: {exc}")

                if fail_line_compact:
                    print(f"FAILED seq={seq} reason={reason_key}")

                if fail_summary_every > 0 and (fail_total % fail_summary_every == 0):
                    print_fail_summary(header=f"fail_summary@{fail_total}")


    async def _one_update(seq: int, client: httpx.AsyncClient) -> None:
        nonlocal stats_ok, stats_failed
        async with sem:
            try:
                async with pool_lock:
                    if not block_pool:
                        raise RuntimeError("No blocks in pool to update")
                    target = random.choice(block_pool[:hotset_size])

                await _update_block(
                    client=client,
                    api_base=api_base,
                    block_id=target,
                    content=_make_content(seq, content_bytes),
                    metadata={"loadgen": True, "seq": seq, "op": "update"},
                )
                stats_ok += 1
            except httpx.HTTPStatusError as exc:
                await _record_http_failure(seq, resp=exc.response)
            except Exception as exc:  # noqa: BLE001
                stats_failed += 1
                reason_key = _classify_failure(status_code=None, body=None, text=None, exc=exc)
                record_failure(reason_key, f"{type(exc).__name__}: {exc}")

                if fail_line_compact:
                    print(f"FAILED seq={seq} reason={reason_key}")

                if fail_summary_every > 0 and (fail_total % fail_summary_every == 0):
                    print_fail_summary(header=f"fail_summary@{fail_total}")


    async def _one_delete(seq: int, client: httpx.AsyncClient) -> None:
        nonlocal stats_ok, stats_failed
        async with sem:
            try:
                async with pool_lock:
                    if not block_pool:
                        raise RuntimeError("No blocks in pool to delete")
                    target = block_pool.pop()

                await _delete_block(client=client, api_base=api_base, block_id=target)
                stats_ok += 1
            except httpx.HTTPStatusError as exc:
                await _record_http_failure(seq, resp=exc.response)
            except Exception as exc:  # noqa: BLE001
                stats_failed += 1
                reason_key = _classify_failure(status_code=None, body=None, text=None, exc=exc)
                record_failure(reason_key, f"{type(exc).__name__}: {exc}")

                if fail_line_compact:
                    print(f"FAILED seq={seq} reason={reason_key}")

                if fail_summary_every > 0 and (fail_total % fail_summary_every == 0):
                    print_fail_summary(header=f"fail_summary@{fail_total}")

    started = time.time()
    timeout = httpx.Timeout(request_timeout_s, connect=min(10.0, request_timeout_s))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if scenario in {"create_then_update", "create_then_delete", "mixed"}:
            print(f"precreate: creating pool_size={pool_size} blocks...")
            for seq in range(1, pool_size + 1):
                await _one_create(seq, client)
                if seq % 200 == 0:
                    print(f"precreate progress: {seq}/{pool_size} ok={stats_ok} failed={stats_failed}")

            async with pool_lock:
                if len(block_pool) < max(1, min(10, pool_size // 10)):
                    print(
                        f"warning: pool has only {len(block_pool)} blocks (requested {pool_size}). "
                        "Update/delete scenarios may be noisy."
                    )

        tasks: list[asyncio.Task[None]] = []
        start_seq = pool_size + 1
        for i in range(0, total_ops):
            seq = start_seq + i

            if scenario == "create":
                op_coro = _one_create(seq, client)
            elif scenario == "create_then_update":
                op_coro = _one_update(seq, client)
            elif scenario == "create_then_delete":
                op_coro = _one_delete(seq, client)
            else:
                r = random.random()
                if r < create_ratio:
                    op_coro = _one_create(seq, client)
                elif r < create_ratio + update_ratio:
                    op_coro = _one_update(seq, client)
                else:
                    op_coro = _one_delete(seq, client)

            tasks.append(asyncio.create_task(op_coro))
            await asyncio.sleep(interval)

            if (i + 1) % 200 == 0:
                elapsed = max(time.time() - started, 1e-6)
                print(
                    f"progress: sent={i+1}/{total_ops} ok={stats_ok} failed={stats_failed} "
                    f"avg_send_rate={(i+1)/elapsed:.1f}/s"
                )

        await asyncio.gather(*tasks)

    elapsed = max(time.time() - started, 1e-6)
    print_fail_summary(header="fail_summary@final")
    print(
        f"done: ok={stats_ok} failed={stats_failed} elapsed={elapsed:.1f}s "
        f"avg_send_rate={total_ops/elapsed:.1f}/s"
    )


if __name__ == "__main__":
    asyncio.run(main())
