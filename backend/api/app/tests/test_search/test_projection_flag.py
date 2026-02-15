import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.app.config.setting import get_settings
from api.app.modules.search.routers.search_router import router as search_router


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_search_returns_empty_when_projection_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_SEARCH_PROJECTION", "false")
    get_settings.cache_clear()

    app = FastAPI()
    app.include_router(search_router, prefix="/api/v1/search")

    client = TestClient(app)
    resp = client.get("/api/v1/search?q=hello")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 0
    assert payload["hits"] == []


def test_search_blocks_returns_empty_when_projection_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_SEARCH_PROJECTION", "0")
    get_settings.cache_clear()

    app = FastAPI()
    app.include_router(search_router, prefix="/api/v1/search")

    client = TestClient(app)
    resp = client.get("/api/v1/search/blocks?q=hello")

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["total"] == 0
    assert payload["hits"] == []
