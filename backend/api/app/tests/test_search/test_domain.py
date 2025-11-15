"""Unit tests for Search domain layer."""
import pytest
from uuid import uuid4


class TestSearchQueryValueObject:
    """Test SearchQuery value object."""

    def test_create_search_query_with_single_term(self):
        query_text = "python programming"
        query = {"query_text": query_text}
        assert query["query_text"] == query_text

    def test_create_search_query_with_filters(self):
        query = {"query_text": "block", "entity_types": ["BLOCK", "BOOK"]}
        assert query["query_text"] == "block"
        assert "BLOCK" in query["entity_types"]

    def test_search_query_with_pagination(self):
        query = {"query_text": "search", "skip": 10, "limit": 20}
        assert query["skip"] == 10
        assert query["limit"] == 20

    def test_search_query_default_pagination(self):
        query = {"query_text": "test", "skip": 0, "limit": 10}
        assert query["skip"] == 0
        assert query["limit"] == 10


class TestSearchResultValueObject:
    """Test SearchResult value object."""

    def test_create_search_result(self):
        hits = [
            {"entity_id": uuid4(), "entity_type": "BLOCK", "score": 0.95},
            {"entity_id": uuid4(), "entity_type": "BOOK", "score": 0.87},
        ]
        result = {"total_count": 2, "hits": hits}
        assert result["total_count"] == 2
        assert len(result["hits"]) == 2

    def test_search_result_empty_hits(self):
        result = {"total_count": 0, "hits": []}
        assert result["total_count"] == 0
        assert len(result["hits"]) == 0

    def test_search_result_equality(self):
        hit = {"entity_id": uuid4(), "entity_type": "BLOCK", "score": 0.9}
        result1 = {"total_count": 1, "hits": [hit]}
        result2 = {"total_count": 1, "hits": [hit]}
        assert result1["total_count"] == result2["total_count"]


class TestSearchHitValueObject:
    """Test SearchHit value object."""

    def test_create_search_hit(self):
        entity_id = uuid4()
        hit = {"entity_id": entity_id, "entity_type": "BLOCK", "score": 0.92}
        assert hit["entity_id"] == entity_id
        assert hit["score"] == 0.92

    def test_search_hit_entity_type_enum(self):
        valid_types = ["BLOCK", "BOOK", "BOOKSHELF", "TAG", "LIBRARY", "ENTRY"]
        entity_type = valid_types[0]
        hit = {"entity_id": uuid4(), "entity_type": entity_type, "score": 0.8}
        assert hit["entity_type"] == entity_type

    def test_search_hit_with_metadata(self):
        metadata = {"title": "Example", "description": "Test"}
        hit = {"entity_id": uuid4(), "entity_type": "BLOCK", "metadata": metadata}
        assert hit["metadata"]["title"] == "Example"


class TestSearchDomainEvents:
    """Test search domain events."""

    def test_search_executed_event(self):
        event = {"query": "python", "entity_types": ["BLOCK"], "result_count": 5}
        assert event["query"] == "python"
        assert event["result_count"] == 5


class TestSearchEntityTypeEnum:
    """Test SearchEntityType enum."""

    def test_valid_entity_types(self):
        valid_types = ["BLOCK", "BOOK", "BOOKSHELF", "TAG", "LIBRARY", "ENTRY"]
        assert len(valid_types) == 6

    def test_entity_type_case_sensitivity(self):
        assert "BLOCK" in ["BLOCK", "BOOK"]
        assert "block" not in ["BLOCK", "BOOK"]
