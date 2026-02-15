"""Experiment 1B: 50k blocks with tags (LIKE + JOIN tags) vs search_index single-table.

What this generates
- A minimal LAB Library/Bookshelf/Book scaffold (same as experiment1)
- N blocks under that book
- M tags with LAB prefix
- Tag associations (entity_type='block') for each block
- Optional: denormalized search_index rows for blocks where `text` includes both block content and tag names

Why this is a good "spaghetti SQL" demo
- Baseline query needs JOIN + DISTINCT (or GROUP BY) because blocks can have multiple tags
- Denormalized query is a single-table scan (still using ILIKE here; index experiments are next)

Usage (PowerShell)
  $env:DATABASE_URL = "postgresql://wordloom:wordloom@localhost:5435/wordloom_test"
  python backend/scripts/labs/experiment1b_generate_blocks_with_tags.py --reset --seed 12345 --count 50000 --tags 500 --tags-per-block 2 --with-search-index

Then run EXPLAIN queries (examples are in the doc template below).
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


LAB_LIBRARY_NAME = "LAB_SEARCH_EXPERIMENT_1B"
LAB_BOOKSHELF_NAME = "LAB_SHELF_EXPERIMENT_1B"
LAB_BOOK_TITLE = "LAB_BOOK_EXPERIMENT_1B"
LAB_TAG_PREFIX = "LAB_TAG_EXP1B_"


@dataclass(frozen=True)
class ScaffoldIds:
    library_id: str
    bookshelf_id: str
    book_id: str
    user_id: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event_version(occurred_at: datetime) -> int:
    return int(occurred_at.timestamp() * 1_000_000)


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
            "SELECT id, user_id FROM libraries WHERE name = %s ORDER BY created_at DESC LIMIT 1",
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
            library_id, user_id = row
            library_id = str(library_id)
            user_id = str(user_id)

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

    return ScaffoldIds(library_id=library_id, bookshelf_id=bookshelf_id, book_id=book_id, user_id=user_id)


def _chunked(seq, chunk_size: int):
    for i in range(0, len(seq), chunk_size):
        yield seq[i : i + chunk_size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, required=True, help="e.g. 50000")
    parser.add_argument("--tags", type=int, default=500, help="how many tags to create")
    parser.add_argument("--tags-per-block", type=int, default=2, help="associations per block")
    parser.add_argument("--keyword", type=str, default="quantum")
    parser.add_argument("--keyword-rate", type=float, default=0.01)
    parser.add_argument(
        "--tag-keyword-rate",
        type=float,
        default=0.01,
        help="fraction of tags whose name includes the keyword (so JOIN+LIKE can match tags too)",
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--with-search-index", action="store_true")
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
                # Delete tag_associations for LAB book blocks
                cur.execute(
                    """
                    DELETE FROM tag_associations
                    WHERE entity_type = 'block'
                      AND entity_id IN (SELECT id FROM blocks WHERE book_id = %s)
                    """,
                    (scaffold.book_id,),
                )
                # Delete search_index for LAB book blocks
                cur.execute(
                    """
                    DELETE FROM search_index
                    WHERE entity_type = 'block'
                      AND entity_id IN (SELECT id FROM blocks WHERE book_id = %s)
                    """,
                    (scaffold.book_id,),
                )
                # Delete blocks
                cur.execute("DELETE FROM blocks WHERE book_id = %s", (scaffold.book_id,))
                # Delete LAB tags (associations already deleted above)
                cur.execute("DELETE FROM tags WHERE user_id = %s AND name LIKE %s", (scaffold.user_id, LAB_TAG_PREFIX + "%"))
            conn.commit()

        # Create tags
        tags = []
        tag_names = []
        for i in range(args.tags):
            tag_id = str(uuid4())
            if random.random() < args.tag_keyword_rate:
                tag_name = f"{LAB_TAG_PREFIX}{i:04d}_{args.keyword}"
            else:
                tag_name = f"{LAB_TAG_PREFIX}{i:04d}"
            tags.append(
                (
                    tag_id,
                    scaffold.user_id,
                    tag_name,
                    "#6366F1",
                    None,  # icon_emoji
                    None,  # description
                    None,  # parent_tag_id
                    0,  # level
                    0,  # usage_count
                    now,
                    now,
                    None,  # deleted_at
                )
            )
            tag_names.append(tag_name)

        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO tags (
                    id, user_id, name, color, icon_emoji, description,
                    parent_tag_id, level, usage_count, created_at, updated_at, deleted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, name) DO NOTHING
                """,
                tags,
            )
        conn.commit()

        # Fetch tag ids back (in case of conflict/do nothing)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name FROM tags WHERE user_id = %s AND name LIKE %s ORDER BY name",
                (scaffold.user_id, LAB_TAG_PREFIX + "%"),
            )
            tag_rows = cur.fetchall()
        tag_by_name = {name: str(tid) for (tid, name) in tag_rows}
        tag_name_pool = list(tag_by_name.keys())

        # Insert blocks + associations (+ optional search_index)
        blocks_sql = """
            INSERT INTO blocks (
                id, book_id, type, content, "order",
                heading_level, soft_deleted_at,
                deleted_prev_id, deleted_next_id, deleted_section_path,
                deleted_at, meta,
                created_at, updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        assoc_sql = """
            INSERT INTO tag_associations (id, tag_id, entity_type, entity_id, created_at)
            VALUES (%s, %s, 'block', %s, %s)
            ON CONFLICT (tag_id, entity_type, entity_id) DO NOTHING
        """

        search_sql = """
            INSERT INTO search_index (
                id, entity_type, entity_id, text, snippet,
                rank_score, created_at, updated_at, event_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (entity_type, entity_id) DO UPDATE
              SET text = EXCLUDED.text,
                  snippet = EXCLUDED.snippet,
                  updated_at = EXCLUDED.updated_at,
                  event_version = EXCLUDED.event_version
              WHERE search_index.event_version <= EXCLUDED.event_version
        """

        chunk_size = 2000
        total = args.count

        for base in range(0, total, chunk_size):
            batch_n = min(chunk_size, total - base)
            block_rows = []
            assoc_rows = []
            search_rows = []

            for i in range(base, base + batch_n):
                block_id = str(uuid4())
                content = _rand_text(i, keyword=args.keyword, keyword_rate=args.keyword_rate)
                order = Decimal(i + 1)

                # sample tags for this block
                chosen = random.sample(tag_name_pool, k=min(args.tags_per_block, len(tag_name_pool)))
                chosen_ids = [tag_by_name[n] for n in chosen]

                block_rows.append(
                    (
                        block_id,
                        scaffold.book_id,
                        "text",
                        content,
                        order,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        now,
                        now,
                    )
                )

                for tid in chosen_ids:
                    assoc_rows.append((str(uuid4()), tid, block_id, now))

                if args.with_search_index:
                    # Denormalize: content + tag names into a single searchable blob.
                    denorm_text = content + " " + " ".join(chosen)
                    search_rows.append(
                        (
                            str(uuid4()),
                            "block",
                            block_id,
                            denorm_text,
                            denorm_text[:200],
                            0.0,
                            now,
                            now,
                            _event_version(now),
                        )
                    )

            with conn.cursor() as cur:
                cur.executemany(blocks_sql, block_rows)
                cur.executemany(assoc_sql, assoc_rows)
                if args.with_search_index and search_rows:
                    cur.executemany(search_sql, search_rows)
            conn.commit()

        print(
            "OK: inserted "
            f"{args.count} blocks, {len(tag_by_name)} tags, "
            f"~{args.count * min(args.tags_per_block, len(tag_by_name))} block-tag associations "
            f"into book={scaffold.book_id}. "
            + ("Also upserted search_index rows." if args.with_search_index else "")
        )


if __name__ == "__main__":
    main()
