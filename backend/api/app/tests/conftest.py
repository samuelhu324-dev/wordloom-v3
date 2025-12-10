"""
Tests-Level Pytest Configuration
=================================

Purpose:
- Provide integration test fixtures specific to test suite
- Setup FastAPI test client
- Provide cross-module test utilities

Scope: Tests directory level

Hierarchy:
- Global (backend/conftest.py): Event loop, pytest config
- App (backend/api/app/conftest.py): Database, sessions, auth mocks
- Tests (this file): FastAPI client, integration utilities
- Modules (backend/api/app/modules/*/conftest.py): Domain-specific factories
"""

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession


# ============================================================================
# FastAPI Test Client
# ============================================================================

# Note: FastAPI TestClient fixture commented out until main.py is populated
# Uncomment when app is ready for HTTP testing
#
# @pytest.fixture
# def test_client():
#     """
#     Create FastAPI test client for HTTP testing
#
#     Returns: TestClient (synchronous HTTP client for FastAPI)
#     """
#     from fastapi.testclient import TestClient
#     from main import app
#     return TestClient(app)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
async def populated_db(db_session: AsyncSession):
    """
    Create a populated test database with sample data

    Note: This fixture requires db_session to already be created

    Scope: function (creates fresh data per test)
    Returns: db_session with sample data
    """
    # Sample data will be created by individual tests
    # This serves as a placeholder for future population logic
    yield db_session


# ============================================================================
# Test Utilities
# ============================================================================

class HTTPAssertions:
    """
    Utility class for common HTTP response assertions
    """

    @staticmethod
    def assert_success(response):
        """Assert response status is 200-299"""
        assert 200 <= response.status_code < 300, \
            f"Expected success, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_created(response):
        """Assert response status is 201 Created"""
        assert response.status_code == 201, \
            f"Expected 201 Created, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_bad_request(response):
        """Assert response status is 400 Bad Request"""
        assert response.status_code == 400, \
            f"Expected 400 Bad Request, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_unauthorized(response):
        """Assert response status is 401 Unauthorized"""
        assert response.status_code == 401, \
            f"Expected 401 Unauthorized, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_not_found(response):
        """Assert response status is 404 Not Found"""
        assert response.status_code == 404, \
            f"Expected 404 Not Found, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_conflict(response):
        """Assert response status is 409 Conflict"""
        assert response.status_code == 409, \
            f"Expected 409 Conflict, got {response.status_code}: {response.text}"

    @staticmethod
    def assert_unprocessable(response):
        """Assert response status is 422 Unprocessable Entity"""
        assert response.status_code == 422, \
            f"Expected 422 Unprocessable Entity, got {response.status_code}: {response.text}"


@pytest.fixture
def http_assertions():
    """
    Provide HTTP assertion utilities

    Returns: HTTPAssertions class

    Usage:
        def test_endpoint(test_client, http_assertions):
            response = test_client.get("/api/libraries")
            http_assertions.assert_success(response)
    """
    return HTTPAssertions()


# ============================================================================
# Pytest Markers
# ============================================================================

def pytest_configure(config):
    """Add tests-level markers"""
    config.addinivalue_line(
        "markers",
        "e2e: mark test as end-to-end (full request/response cycle)"
    )
    config.addinivalue_line(
        "markers",
        "http: mark test as testing HTTP endpoints"
    )
