"""Experiment 1: Generate 5k/50k blocks (and optional search_index rows) for query benchmarking.

This script targets the DEVTEST-DB-5435 database by default (via DATABASE_URL).
It creates a minimal Library/Bookshelf/Book scaffold (LAB_* names) if none exists,
then inserts blocks referencing that book.

Why not rely on ORM defaults?
- These tables were created with NOT NULL timestamps but no server defaults.
  So for direct SQL inserts we must supply created_at/updated_at.

Usage:
  $env:DATABASE_URL = "postgresql://wordloom:wordloom@localhost:5435/wordloom_test"
  python backend/scripts/labs/experiment1_generate_blocks.py --count 5000
  python backend/scripts/labs/experiment1_generate_blocks.py --count 50000 --keyword-rate 0.02

After generation, run EXPLAIN ANALYZE queries:
  - blocks baseline: WHERE content ILIKE '%quantum%'
  - search_index: WHERE entity_type='block' AND text ILIKE '%quantum%'
"""

from __future__ import annotations

import argparse
import os
import random
import string
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import psycopg


LAB_LIBRARY_NAME = "LAB_SEARCH_EXPERIMENT_1"
LAB_BOOKSHELF_NAME = "LAB_SHELF_EXPERIMENT_1"
LAB_BOOK_TITLE = "LAB_BOOK_EXPERIMENT_1"


@dataclass(frozen=True)
class ScaffoldIds:
    library_id: str
    bookshelf_id: str
    book_id: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _rand_text(i: int, *, keyword: str, keyword_rate: float) -> str:
    base = f"block-{i} " + "".join(random.choices(string.ascii_lowercase + " ", k=220))
    if random.random() < keyword_rate:
        return base + f" {keyword}"
    return base


def _get_or_create_scaffold(conn: psycopg.Connection) -> ScaffoldIds:
    now = _now()

    with conn.cursor() as cur:
        # Library
        cur.execute(
            "SELECT id FROM libraries WHERE name = %s ORDER BY created_at DESC LIMIT 1",
            (LAB_LIBRARY_NAME,),
        )
        row = cur.fetchone()
        if row is None:
            library_id = str(uuid4())
            user_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO libraries (
                    id, user_id, basement_bookshelf_id, name, description, cover_media_id,
                    theme_color, pinned, pinned_order, archived_at, last_activity_at,
                    views_count, last_viewed_at, created_at, updated_at, soft_deleted_at
                )
                VALUES (
                    %s, %s, NULL, %s, NULL, NULL,
                    NULL, FALSE, NULL, NULL, %s,
                    0, NULL, %s, %s, NULL
                )
                """,
                (library_id, user_id, LAB_LIBRARY_NAME, now, now, now),
            )
        else:
            (library_id,) = row
            library_id = str(library_id)

        # Bookshelf
        cur.execute(
            """
            SELECT id FROM bookshelves
            WHERE library_id = %s AND name = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (library_id, LAB_BOOKSHELF_NAME),
        )
        row = cur.fetchone()
        if row is None:
            bookshelf_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO bookshelves (
                    id, library_id, name, description,
                    is_basement, is_pinned, pinned_at, is_favorite,
                    status, book_count, created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, NULL,
                    FALSE, FALSE, NULL, FALSE,
                    'active', 0, %s, %s
                )
                """,
                (bookshelf_id, library_id, LAB_BOOKSHELF_NAME, now, now),
            )
        else:
            (bookshelf_id,) = row
            bookshelf_id = str(bookshelf_id)

        # Book
        cur.execute(
            """
            SELECT id FROM books
            WHERE library_id = %s AND bookshelf_id = %s AND title = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (library_id, bookshelf_id, LAB_BOOK_TITLE),
        )
        row = cur.fetchone()
        if row is None:
            book_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO books (
                    id, bookshelf_id, library_id,
                    title, summary, cover_icon, cover_media_id,
                    is_pinned, due_at, status, maturity,
                    block_count, maturity_score, legacy_flag,
                    manual_maturity_override, manual_maturity_reason,
                    last_visited_at, visit_count_90d,
                    previous_bookshelf_id, moved_to_basement_at, soft_deleted_at,
                    created_at, updated_at
                )
                VALUES (
                    %s, %s, %s,
                    %s, NULL, NULL, NULL,
                    FALSE, NULL, 'draft', 'seed',
                    0, 0, FALSE,
                    FALSE, NULL,
                    NULL, 0,
                    NULL, NULL, NULL,
                    %s, %s
                )
                """,
                (book_id, bookshelf_id, library_id, LAB_BOOK_TITLE, now, now),
            )
        else:
            (book_id,) = row
            book_id = str(book_id)

    return ScaffoldIds(library_id=library_id, bookshelf_id=bookshelf_id, book_id=book_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True, help="e.g. 5000 or 50000")
    parser.add_argument("--keyword", type=str, default="quantum", help="keyword used in ILIKE benchmark")
    parser.add_argument("--keyword-rate", type=float, default=0.01, help="fraction of blocks containing keyword")
    parser.add_argument("--seed", type=int, default=0, help="random seed (0 means do not set)")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing LAB book blocks (and their search_index rows) before inserting new ones.",
    )
    parser.add_argument(
        "--with-search-index",
        action="store_true",
        help="Also insert matching search_index rows for the generated blocks.",
    )
    args = parser.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise SystemExit("DATABASE_URL is required")

    if args.seed:
        random.seed(args.seed)

    now = _now()

    with psycopg.connect(dsn) as conn:
        conn.execute("SET TIME ZONE 'UTC'")
        scaffold = _get_or_create_scaffold(conn)

        if args.reset:
            with conn.cursor() as cur:
                # Remove search_index rows first (avoid orphaned index entries).
                cur.execute(
                    """
                    DELETE FROM search_index
                    WHERE entity_type = 'block'
                      AND entity_id IN (SELECT id FROM blocks WHERE book_id = %s)
                    """,
                    (scaffold.book_id,),
                )
                cur.execute("DELETE FROM blocks WHERE book_id = %s", (scaffold.book_id,))
            conn.commit()

        blocks = []
        search_rows = []
        for i in range(args.count):
            block_id = str(uuid4())
            content = _rand_text(i, keyword=args.keyword, keyword_rate=args.keyword_rate)
            order = Decimal(i + 1)
            blocks.append(
                (
                    block_id,
                    scaffold.book_id,
                    "text",
                    content,
                    order,
                    None,  # heading_level
                    None,  # soft_deleted_at
                    None,  # deleted_prev_id
                    None,  # deleted_next_id
                    None,  # deleted_section_path
                    None,  # deleted_at
                    None,  # meta
                    now,
                    now,
                )
            )
            if args.with_search_index:
                event_version = int(now.timestamp() * 1_000_000)
                search_rows.append(
                    (
                        str(uuid4()),
                        "block",
                        block_id,
                        content,
                        content[:200],
                        0.0,
                        now,
                        now,
                        event_version,
                    )
                )

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO blocks (
                    id, book_id, type, content, "order",
                    heading_level, soft_deleted_at,
                    deleted_prev_id, deleted_next_id, deleted_section_path,
                    deleted_at, meta,
                    created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                blocks,
            )

            if args.with_search_index and search_rows:
                cur.executemany(
                    """
                    INSERT INTO search_index (
                        id, entity_type, entity_id, text, snippet,
                        rank_score, created_at, updated_at, event_version
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (entity_type, entity_id) DO NOTHING
                    """,
                    search_rows,
                )

        conn.commit()

    print(
        f"OK: inserted {args.count} blocks into book={scaffold.book_id}. "
        + ("Also inserted search_index rows." if args.with_search_index else "")
    )


if __name__ == "__main__":
    main()
