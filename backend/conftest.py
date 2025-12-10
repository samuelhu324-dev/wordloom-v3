"""
Global Pytest Configuration - Root Level
==========================================

Purpose:
- Set event loop policy for Windows + psycopg3 compatibility
- Create async event loop for all tests
- Configure pytest markers and hooks globally

Scope: Session-level (shared across all modules)

CRITICAL: Event loop policy MUST be set in pytest_configure before any async operations!
"""

import pytest
import asyncio
import sys


# ============================================================================
# Setup Event Loop Policy (BEFORE creating any loops)
# ============================================================================

def pytest_configure(config):
    """
    Global pytest configuration - runs before any tests

    Sets up event loop policy on Windows for psycopg3 compatibility
    """
    # Set event loop policy FIRST
    if sys.platform == 'win32':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("\n[OK] pytest: WindowsSelectorEventLoopPolicy set")
        except Exception as e:
            print(f"\n[!] pytest: Warning - Could not set event loop policy: {e}")
    else:
        print("\n[OK] pytest: Using default event loop policy (Unix-like)")

    # Register custom markers
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


# ============================================================================
# Event Loop Management
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create and configure event loop for async tests

    Scope: session (one loop for all tests)

    Required for pytest-asyncio to run async tests properly.
    NOTE: Event loop policy is already set in pytest_configure
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    yield loop
    loop.close()


# ============================================================================
# Test Collection Modification
# ============================================================================

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