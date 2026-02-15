from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.search.application.ports.candidate_provider import Candidate


class PostgresFTSCandidateProvider:
    """Stage1 recall using Postgres FTS over `search_index`.

    This is the current production implementation (before Elastic).
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_block_candidates(self, *, q: str, candidate_limit: int) -> list[Candidate]:
        sql = text(
            """
            SELECT
                si.entity_id AS entity_id,
                COALESCE(
                    ts_headline(
                        'english',
                        si.text,
                        plainto_tsquery('english', :q),
                        'MaxFragments=2,MinWords=3,MaxWords=15,ShortWord=3,HighlightAll=FALSE'
                    ),
                    ''
                ) AS snippet,
                ts_rank_cd(
                    to_tsvector('english', si.text),
                    plainto_tsquery('english', :q)
                ) AS score,
                si.event_version AS order_key
            FROM search_index si
            WHERE si.entity_type = 'block'
              AND to_tsvector('english', si.text) @@ plainto_tsquery('english', :q)
            ORDER BY si.event_version DESC
            LIMIT :candidate_limit
            """
        )

        rows = (
            await self._session.execute(sql, {"q": q, "candidate_limit": candidate_limit})
        ).mappings().all()

        return [
            Candidate(
                entity_id=row["entity_id"],
                snippet=row.get("snippet") or "",
                score=float(row["score"]) if row.get("score") is not None else None,
                order_key=int(row["order_key"]),
            )
            for row in rows
        ]


__all__ = ["PostgresFTSCandidateProvider"]
