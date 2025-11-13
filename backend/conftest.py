"""
Global Pytest Configuration - Root Level
==========================================

Purpose:
- Create async event loop for all tests
- Configure pytest markers and hooks globally

Scope: Session-level (shared across all modules)

Note: Database engine fixture is defined in backend/api/app/conftest.py
because it requires importing Base from the app package.
"""

import pytest
import asyncio


# ============================================================================
# Event Loop Management
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create and configure event loop for async tests

    Scope: session (one loop for all tests)

    Required for pytest-asyncio to run async tests properly.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    yield loop
    loop.close()


# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """
    Global pytest configuration

    Registers custom markers and configuration
    """
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async (automatically handled by pytest-asyncio)"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (tests multiple modules)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow (may take longer to execute)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection

    Automatically add asyncio marker to async tests
    """
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# ============================================================================
# Logging Configuration
# ============================================================================

import logging

logging.basicConfig(
    level=logging.WARNING,  # Reduce noise during tests
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Reduce verbosity from libraries
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
