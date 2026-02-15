from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from api.app.modules.search.application.ports.candidate_provider import Candidate

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _ElasticConfig:
    base_url: str
    index: str


def _get_config() -> _ElasticConfig:
    base_url = (os.getenv("ELASTIC_URL") or "http://localhost:9200").rstrip("/")
    index = os.getenv("ELASTIC_INDEX") or "wordloom-search-index"
    return _ElasticConfig(base_url=base_url, index=index)


def _http_json(method: str, url: str, body: dict[str, Any] | None) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(url, data=data, method=method)
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urlopen(req, timeout=5) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Elastic HTTPError {e.code} for {url}: {detail}") from e
    except URLError as e:
        raise RuntimeError(f"Elastic connection failed for {url}: {e}") from e


class ElasticCandidateProvider:
    """Stage1 recall using Elasticsearch.

    Requires ES docs contain:
      - entity_type: 'block'
      - entity_id: UUID string
      - text: searchable text
      - snippet: optional
      - event_version: bigint (used as order_key)

    Env:
      - ELASTIC_URL (default http://localhost:9200)
      - ELASTIC_INDEX (default wordloom-search-index)
    """

    def __init__(self):
        self._cfg = _get_config()

    async def get_block_candidates(self, *, q: str, candidate_limit: int) -> list[Candidate]:
        url = f"{self._cfg.base_url}/{self._cfg.index}/_search"

        query = {
            "size": candidate_limit,
            "track_total_hits": False,
            "query": {
                "bool": {
                    "filter": [{"term": {"entity_type": "block"}}],
                    "must": [
                        {
                            "match": {
                                "text": {
                                    "query": q,
                                    "operator": "and",
                                }
                            }
                        }
                    ],
                }
            },
            "sort": [{"event_version": {"order": "desc"}}],
            "highlight": {
                "fields": {
                    "text": {
                        "number_of_fragments": 1,
                        "fragment_size": 200,
                        "pre_tags": [""],
                        "post_tags": [""],
                    }
                }
            },
            "_source": ["entity_id", "snippet", "event_version"],
        }

        resp = _http_json("POST", url, query)
        hits = ((resp.get("hits") or {}).get("hits")) or []

        candidates: list[Candidate] = []
        for hit in hits:
            src = hit.get("_source") or {}
            entity_id_raw = src.get("entity_id")
            if not entity_id_raw:
                continue

            try:
                entity_id = UUID(str(entity_id_raw))
            except Exception:
                continue

            event_version = int(src.get("event_version") or 0)
            score = hit.get("_score")

            hl = (hit.get("highlight") or {}).get("text") or []
            snippet = (hl[0] if hl else None) or (src.get("snippet") or "")

            candidates.append(
                Candidate(
                    entity_id=entity_id,
                    order_key=event_version,
                    snippet=snippet,
                    score=float(score) if score is not None else None,
                )
            )

        logger.info(
            {
                "event": "search.stage1.elastic.recalled",
                "count": len(candidates),
            }
        )
        return candidates


__all__ = ["ElasticCandidateProvider"]
