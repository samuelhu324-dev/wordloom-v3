from __future__ import annotations

from typing import List
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.search.application.dtos import BlockSearchHit
from api.app.modules.search.application.ports.candidate_provider import CandidateProvider


class TwoStageSearchService:
    """Two-stage search workflow (search-only).

    Stage1: candidate recall from CandidateProvider (Postgres FTS now, Elastic later).
    Stage2: strict business filter/joins in Postgres (blocks + tags).

    This service is intentionally separate from the existing SearchPort / usecase
    to avoid contract changes.
    """

    def __init__(self, session: AsyncSession, candidate_provider: CandidateProvider):
        self._session = session
        self._candidate_provider = candidate_provider

    async def search_block_hits(
        self,
        *,
        q: str,
        book_id: UUID | None,
        limit: int,
        candidate_limit: int,
    ) -> List[BlockSearchHit]:
        candidates = await self._candidate_provider.get_block_candidates(
            q=q, candidate_limit=candidate_limit
        )
        if not candidates:
            return []

        # Stage2: join blocks + tag_associations + tags with business filters.
        # Feed candidates through unnest arrays to avoid dynamic SQL.
        block_ids = [c.entity_id for c in candidates]
        snippets = [c.snippet for c in candidates]
        scores = [c.score for c in candidates]
        order_keys = [c.order_key for c in candidates]

        sql = text(
            """
            WITH candidate_blocks AS (
                SELECT *
                FROM unnest(
                    CAST(:block_ids AS uuid[]),
                    CAST(:snippets AS text[]),
                    CAST(:scores AS float8[]),
                    CAST(:order_keys AS bigint[])
                ) AS c(block_id, snippet, score, order_key)
            )
            SELECT
                c.block_id AS id,
                COALESCE(NULLIF(c.snippet, ''), LEFT(b.content, 200)) AS snippet,
                c.score AS score,
                array_remove(array_agg(DISTINCT t.name), NULL) AS tags
            FROM candidate_blocks c
            JOIN blocks b
                ON b.id = c.block_id
            LEFT JOIN tag_associations ta
                ON ta.entity_type = 'block' AND ta.entity_id = b.id
            LEFT JOIN tags t
                ON t.id = ta.tag_id AND t.deleted_at IS NULL
            WHERE b.soft_deleted_at IS NULL
                AND (:book_id IS NULL OR b.book_id = CAST(:book_id AS uuid))
            GROUP BY c.block_id, c.snippet, c.score, c.order_key, b.content
            ORDER BY c.order_key DESC
            LIMIT :limit
            """
        )

        rows = (
            await self._session.execute(
                sql,
                {
                    "block_ids": block_ids,
                    "snippets": snippets,
                    "scores": scores,
                    "order_keys": order_keys,
                    "book_id": book_id,
                    "limit": limit,
                },
            )
        ).mappings().all()

        hits: List[BlockSearchHit] = []
        for row in rows:
            tags = row.get("tags") or []
            hits.append(
                BlockSearchHit(
                    id=row["id"],
                    snippet=row.get("snippet"),
                    score=float(row["score"]) if row.get("score") is not None else None,
                    tags=list(tags),
                )
            )
        return hits


__all__ = ["TwoStageSearchService"]
