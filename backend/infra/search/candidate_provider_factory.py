from __future__ import annotations

import logging
import os

from sqlalchemy.ext.asyncio import AsyncSession

from api.app.modules.search.application.ports.candidate_provider import CandidateProvider
from infra.search.postgres_fts_candidate_provider import PostgresFTSCandidateProvider
from infra.search.elastic_candidate_provider import ElasticCandidateProvider

logger = logging.getLogger(__name__)


def get_stage1_candidate_provider(session: AsyncSession) -> CandidateProvider:
    """Factory for Stage1 candidate providers.

    Controlled by env var:
      - SEARCH_STAGE1_PROVIDER=postgres|elastic

    Default is postgres to preserve current behavior.
    """

    provider = (os.getenv("SEARCH_STAGE1_PROVIDER") or "postgres").strip().lower()

    if provider == "postgres":
        selected: CandidateProvider = PostgresFTSCandidateProvider(session)
    elif provider == "elastic":
        selected = ElasticCandidateProvider()
    else:
        raise ValueError(f"Unknown SEARCH_STAGE1_PROVIDER={provider!r}")

    logger.info(
        {
            "event": "search.stage1.provider.selected",
            "provider": provider,
        }
    )
    return selected


__all__ = ["get_stage1_candidate_provider"]
