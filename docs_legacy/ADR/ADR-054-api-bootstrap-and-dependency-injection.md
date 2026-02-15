# ADR-054: API Bootstrap and Dependency Injection Architecture

**Date:** November 15, 2025
**Status:** ✅ **ACCEPTED**
**Author:** Wordloom Architecture Team
**Related ADRs:** ADR-050 (Hexagonal Architecture), ADR-051 (DDD Principles), ADR-053 (Database Schema)

---

## Executive Summary

This ADR documents the FastAPI bootstrap implementation and Dependency Injection (DI) container architecture that enables the Wordloom API to start successfully in minimal mode while maintaining modular infrastructure for future router and endpoint implementation.

**Context:** After successful PostgreSQL database schema initialization (ADR-053), the API bootstrap encountered import path conflicts between the `backend/api` application layer and `backend/infra` infrastructure layer. This ADR records the architectural decisions that resolved these conflicts and established a resilient bootstrap pattern.

---

## Context

### Problem Statement

1. **Import Path Conflicts**: The FastAPI application (`backend/api/app/`) required access to infrastructure layer modules (`backend/infra/database/`, `backend/infra/storage/`) without modifying Python's module search path.

2. **Missing Infrastructure Files**: The dependency injection container and database session factory were not yet implemented, leaving the application unable to resolve service dependencies.

3. **Graceful Degradation Need**: The system needed to bootstrap successfully even when optional infrastructure components (routers, event handlers) were not yet fully implemented.

4. **Production Readiness**: The API needed to respond to health checks and handle CORS requests from the Next.js frontend on localhost:3000 before all business logic endpoints were implemented.

### Current State

- **Database**: ✅ PostgreSQL initialized with 11 tables (ADR-053)
- **Frontend**: ✅ Next.js 14 bootstrapped with 43 files and 3-theme system
- **Backend**: ⏳ FastAPI bootstrapped in minimal mode (0/6 routers loaded)
- **Port Configuration**: API on localhost:30001, Frontend on localhost:3000

---

## Decision

We **ACCEPT** the following architectural pattern for API bootstrap and dependency injection:

### 1. **Modified sys.path Initialization in main.py**

```python
# File: backend/api/app/main.py
import sys
from pathlib import Path

# Add paths for cross-module imports
backend_root = Path(__file__).resolve().parents[3] / "backend"
api_root = Path(__file__).resolve().parents[2]

if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
if str(api_root) not in sys.path:
    sys.path.insert(0, str(api_root))
```

**Rationale**: Explicit path management prevents import conflicts and makes module resolution clear during development and testing.

---

### 2. **Dependency Injection Container Pattern**

**File**: `backend/api/app/dependencies.py`

```python
from typing import Any, Dict, Optional

class DIContainer:
    """Dependency Injection container for service registration and retrieval."""

    _instance = None
    _services: Dict[str, Any] = {}
    _factories: Dict[str, callable] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self._services[name] = service

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function for lazy initialization."""
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        """Retrieve a registered service or factory result."""
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            return self._factories[name]()
        raise KeyError(f"Service '{name}' not found in DI container")

    def clear(self) -> None:
        """Clear all registrations (for testing)."""
        self._services.clear()
        self._factories.clear()

def get_di_container() -> DIContainer:
    """Get the global DI container instance."""
    return DIContainer()

async def get_di_container_provider():
    """FastAPI dependency provider for DI container."""
    yield get_di_container()
```

**Design Decisions**:
- **Singleton Pattern**: Single instance across application lifetime
- **Factory Registration**: Support lazy initialization for expensive services
- **FastAPI Compatible**: Dependency provider function for FastAPI's `Depends()` injection
- **Clear API**: Simple `register()` and `get()` methods

---

### 3. **Async Database Session Management**

**File**: `backend/infra/database/session.py`

```python
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:pgpass@127.0.0.1:5433/wordloom"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db_session():
    """FastAPI dependency for database session injection."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**Design Decisions**:
- **AsyncIO Compatible**: Matches FastAPI's async-first architecture
- **Connection Pooling**: Pool size 10 with max overflow 20 for concurrent requests
- **Context Manager**: Automatic session cleanup via `async with`
- **Environment Variable**: DATABASE_URL configurable, with sensible default

---

### 4. **Graceful Degradation in Startup Events**

**File**: `backend/api/app/main.py` (lifespan events)

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI application lifecycle."""
    # Startup
    logger.info("Starting Wordloom API...")
    try:
        # Load routers (if available)
        try:
            from api.modules.library.routers import router as library_router
            app.include_router(library_router)
            logger.info("✅ Loaded library router")
        except ImportError as e:
            logger.warning(f"⚠️ Could not load library router: {e}")

        # Similar pattern for other routers...

    except Exception as e:
        logger.error(f"⚠️ Infrastructure warning (non-blocking): {e}")

    logger.info(f"API ready on http://0.0.0.0:30001")
    yield

    # Shutdown
    logger.info("Shutting down Wordloom API...")

app = FastAPI(
    title="Wordloom API",
    version="1.0.0",
    lifespan=lifespan,
)
```

**Rationale**:
- **Try/Except Blocks**: Router import failures don't crash the API
- **Informative Logging**: Warnings help identify missing implementations
- **Minimal Mode**: API runs successfully even with 0 routers loaded
- **Structured Lifecycle**: Clear startup and shutdown phases

---

### 5. **Infrastructure File Exports**

**File**: `backend/infra/database/__init__.py`

```python
from .base import Base  # SQLAlchemy declarative base
from .models import (
    LibraryModel,
    BookshelfModel,
    BookModel,
    BlockModel,
    TagModel,
    MediaModel,
    SearchIndexModel,
    ChronicleModel,
)
from .session import AsyncSessionLocal, get_db_session, engine

__all__ = [
    "Base",
    "LibraryModel",
    "BookshelfModel",
    "BookModel",
    "BlockModel",
    "TagModel",
    "MediaModel",
    "SearchIndexModel",
    "ChronicleModel",
    "AsyncSessionLocal",
    "get_db_session",
    "engine",
]
```

**Benefits**:
- **Single Import Point**: `from infra.database import LibraryModel` works cleanly
- **Explicit Exports**: `__all__` prevents accidental exposure of internal utilities
- **Scalability**: Easy to add new models without changing import statements

---

## Implementation

### Files Created (Nov 15, 2025)

1. **backend/api/app/dependencies.py** (149 lines)
   - DIContainer class with singleton pattern
   - Factory registration support
   - FastAPI dependency provider

2. **backend/infra/database/session.py** (39 lines)
   - AsyncSessionLocal factory
   - get_db_session() dependency
   - Environment-based configuration

3. **backend/infra/database/models/__init__.py** (35 lines)
   - All 8 ORM models exported
   - Replaces incomplete __init__.py

### Files Modified (Nov 15, 2025)

1. **backend/api/app/main.py**
   - Added sys.path setup for cross-module imports
   - Added lifespan context manager
   - Added CORS middleware configuration
   - Added structured exception handling

2. **backend/infra/database/__init__.py**
   - Added model exports
   - Added session and engine exports
   - Added __all__ declaration

---

## Verification

### Health Check Test

```bash
# Test command
curl http://localhost:30001/health

# Expected response (Nov 15, 2025, 14:32 UTC)
{
  "status": "healthy",
  "version": "1.0.0",
  "infrastructure_available": true,
  "routers_loaded": 0
}
```

### Database Connection Test

```bash
# Test database session from Python
python -c "
from backend.infra.database import AsyncSessionLocal, engine
print('✅ AsyncSessionLocal:', AsyncSessionLocal)
print('✅ Engine:', engine)
print('✅ Connection pool:', engine.pool)
"
```

### Import Path Test

```bash
cd backend/api/app
python -c "
import sys
sys.path.insert(0, '../../')
sys.path.insert(0, '..')
from infra.database import LibraryModel
print('✅ Cross-module import successful:', LibraryModel)
"
```

---

## Consequences

### Positive

✅ **API Bootstrap Successful**: FastAPI responds on localhost:30001 in minimal mode
✅ **Infrastructure Ready**: Database sessions, DI container, async patterns established
✅ **Graceful Degradation**: Missing routers don't crash the API
✅ **Frontend Integration Path Clear**: Next.js can connect to /health endpoint
✅ **Week 2 Preparation**: Router implementations can follow established patterns
✅ **Production Pattern**: Minimal mode enables staged endpoint rollout

### Trade-offs

⚠️ **Manual sys.path Management**: Future Python version changes might affect import behavior
⚠️ **0 Routers Loaded**: Business logic endpoints not yet implemented
⚠️ **Import Warnings**: Router loading warnings appear in logs (non-blocking, informative)

### Mitigation

- Document sys.path setup in bootstrap documentation
- Schedule Week 2 router loading and endpoint implementation
- Add warning suppression if logs become too verbose

---

## Related Decisions

- **ADR-050**: Hexagonal Architecture pattern used for DI container and adapter design
- **ADR-051**: DDD principles inform service registration and domain segregation
- **ADR-053**: Database schema and AsyncAlchemy configuration foundation
- **ADR-052**: Future testing strategy will validate DI container injection

---

## Timeline

| Date | Event |
|------|-------|
| Nov 14, 2025 | Database schema initialized (ADR-053) |
| Nov 15, 09:00 | Import path conflicts identified |
| Nov 15, 10:30 | DI container pattern designed |
| Nov 15, 11:00 | Database session management implemented |
| Nov 15, 12:00 | sys.path fixes applied |
| Nov 15, 14:32 | ✅ API bootstrap successful, /health endpoint verified |
| Week 2 | Router loading and endpoint implementation planned |

---

## References

- **Database Session Documentation**: `backend/infra/database/session.py`
- **DI Container Implementation**: `backend/api/app/dependencies.py`
- **API Bootstrap Code**: `backend/api/app/main.py`
- **Model Exports**: `backend/infra/database/models/__init__.py`
- **Integration Verification**: Health check endpoint at `/health`

---

## Approval

- **Architecture Team**: ✅ Approved (Nov 15, 2025)
- **Database Admin**: ✅ Verified async session compatibility
- **Frontend Lead**: ✅ Confirmed API connectivity requirements met
- **DevOps**: ✅ Port 30001 configuration validated

---

## Next Steps (Week 2)

1. Fix router import paths in `backend/api/app/modules/*/routers/`
2. Implement all 42 API endpoints across 6 modules
3. Register routers in DIContainer during startup
4. Connect frontend TanStack Query to backend endpoints
5. Execute end-to-end integration tests

---

**ADR-054 Status**: ✅ **COMPLETE & IMPLEMENTED** (Nov 15, 2025)
