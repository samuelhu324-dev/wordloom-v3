"""
Unified Event Loop Policy Management

Windows requires SelectorEventLoop for async database drivers (asyncpg).
This module sets the event loop policy ONCE during application startup.

CRITICAL: This should be called before ANY other imports that use asyncio.
"""

import sys
import asyncio


def setup_event_loop_policy():
    """
    Configure event loop policy based on platform.

    On Windows: Use WindowsSelectorEventLoopPolicy to avoid ProactorEventLoop conflicts
    On Unix: Use default policy (already optimal)

    CALL THIS ONLY ONCE at application startup, BEFORE importing other modules!
    """
    if sys.platform == 'win32':
        try:
            # Windows: Use SelectorEventLoop for async database compatibility
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            print("[OK] Event Loop Policy: WindowsSelectorEventLoopPolicy (Windows)")
            return True
        except Exception as e:
            print(f"[!] Warning: Failed to set WindowsSelectorEventLoopPolicy: {e}")
            return False
    else:
        # Unix/Linux/Mac: Default policy is fine
        print("[OK] Event Loop Policy: Default (Unix-like system)")
        return True


__all__ = ["setup_event_loop_policy"]
