from __future__ import annotations

from api.app.modules.search.application.ports.candidate_provider import Candidate


class FakeElasticCandidateProvider:
    """Dev/test provider to simulate Elastic Stage1 recall.

    Intentionally simple: returns preconfigured candidates and only applies the
    requested candidate_limit.
    """

    def __init__(self, candidates: list[Candidate]):
        self._candidates = list(candidates)

    async def get_block_candidates(self, *, q: str, candidate_limit: int) -> list[Candidate]:
        return self._candidates[:candidate_limit]


__all__ = ["FakeElasticCandidateProvider"]
