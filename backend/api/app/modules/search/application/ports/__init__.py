"""
Search Application Ports

Input ports (use case interfaces):
- ExecuteSearchUseCase: Orchestrates search across all entities

Output ports (repository interface):
- SearchPort: Abstract interface for search backend implementation
             Can be implemented via PostgreSQL, Elasticsearch, OpenSearch, etc.
"""

from .input import ExecuteSearchUseCase
from .output import SearchPort

__all__ = [
    # Input port use cases
    "ExecuteSearchUseCase",
    # Output port
    "SearchPort",
]
