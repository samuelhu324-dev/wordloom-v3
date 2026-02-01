"""
Search Application Ports

Input ports (use case interfaces):
- ExecuteSearchUseCase: Orchestrates search across all entities

Output ports (repository interface):
- SearchPort: Abstract interface for search backend implementation
             Can be implemented via PostgreSQL, Elasticsearch, OpenSearch, etc.
"""

from .input import ExecuteSearchUseCase
from .candidate_provider import Candidate, CandidateProvider
from .output import SearchPort

__all__ = [
    # Input port use cases
    "ExecuteSearchUseCase",
    # Output port
    "SearchPort",
    # Two-stage Stage1 port
    "Candidate",
    "CandidateProvider",
]
