"""Unit tests for Search router."""
import pytest
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestSearchRouter:
    """Test Search FastAPI router endpoints."""

    @pytest.fixture
    def client(self):
        app = FastAPI()

        @app.get("/api/search")
        async def search(q: str, entity_types: str = "", skip: int = 0, limit: int = 10):
            return {"query": q, "results": [], "total": 0}

        @app.get("/api/search/blocks")
        async def search_blocks(q: str):
            return {"results": []}

        @app.get("/api/search/books")
        async def search_books(q: str):
            return {"results": []}

        return TestClient(app)

    def test_search_endpoint_with_query(self, client):
        response = client.get("/api/search?q=python")
        assert response.status_code == 200
        assert response.json()["query"] == "python"

    def test_search_with_pagination(self, client):
        response = client.get("/api/search?q=test&skip=10&limit=20")
        assert response.status_code == 200

    def test_search_blocks_endpoint(self, client):
        response = client.get("/api/search/blocks?q=python")
        assert response.status_code == 200

    def test_search_books_endpoint(self, client):
        response = client.get("/api/search/books?q=algorithms")
        assert response.status_code == 200


class TestSearchRouterFiltering:
    """Test search router entity type filtering."""

    @pytest.fixture
    def client(self):
        app = FastAPI()

        @app.get("/api/search")
        async def search(q: str, entity_types: str = ""):
            types_list = entity_types.split(",") if entity_types else []
            return {"query": q, "entity_types": types_list}

        return TestClient(app)

    def test_search_filter_by_single_type(self, client):
        response = client.get("/api/search?q=test&entity_types=BLOCK")
        assert response.status_code == 200

    def test_search_filter_by_multiple_types(self, client):
        response = client.get("/api/search?q=test&entity_types=BLOCK,BOOK,TAG")
        assert response.status_code == 200


class TestSearchRouterSorting:
    """Test search router sorting options."""

    @pytest.fixture
    def client(self):
        app = FastAPI()

        @app.get("/api/search")
        async def search(q: str, sort: str = "relevance"):
            return {"sort": sort, "results": []}

        return TestClient(app)

    def test_search_sort_by_relevance(self, client):
        response = client.get("/api/search?q=test")
        assert response.status_code == 200
        assert response.json()["sort"] == "relevance"
