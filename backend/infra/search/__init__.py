"""Search infrastructure utilities.

This package contains infrastructure components related to search maintenance,
like indexing implementations used by EventBus handlers.
"""

from .search_indexer import SearchIndexer, PostgresSearchIndexer, get_search_indexer
from .candidate_provider_factory import get_stage1_candidate_provider
from .postgres_fts_candidate_provider import PostgresFTSCandidateProvider
from .elastic_candidate_provider import ElasticCandidateProvider
from .fake_elastic_candidate_provider import FakeElasticCandidateProvider

__all__ = [
    "SearchIndexer",
    "PostgresSearchIndexer",
    "get_search_indexer",
    "get_stage1_candidate_provider",
    "PostgresFTSCandidateProvider",
    "ElasticCandidateProvider",
    "FakeElasticCandidateProvider",
]
