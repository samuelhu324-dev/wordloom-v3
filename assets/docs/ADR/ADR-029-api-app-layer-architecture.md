# ADR-028: Application Layer Architecture (core/config/shared/modules)

**Status**: DECIDED ✅
**Date**: 2025-11-13
**Deciders**: Architecture Team
**Related Documents**:
- HEXAGONAL_RULES.yaml (Part 1: Ports & Adapters)
- DDD_RULES.yaml (library domain specification)
- ADR-027: System Rules Consolidation

---

## Context

The Wordloom backend follows Hexagonal Architecture (Ports & Adapters) with Domain-Driven Design (DDD). After migrating to Step 8 (DI Container + Routers), we discovered confusion about:

1. **`backend/api/app/core/`** - Contains database.py and security.py (infrastructure config)
2. **`backend/api/app/config/`** - Should be the single source of configuration
3. **`backend/api/app/infra/`** - Duplicate of backend/infra/ (should be deleted)
4. **`backend/api/app/shared/`** - Cross-module reusable code
5. **`backend/api/app/modules/`** - Domain modules (library, bookshelf, book, etc.)

### Problem Statement

- ❌ Inconsistent file organization at `api/app/` level
- ❌ `core/` and `config/` roles unclear
- ❌ `api/app/infra/` duplicates `backend/infra/`
- ❌ `shared/` incomplete (missing errors.py, deps.py content)
- ❌ No clear architectural rules documented

### Related Issues

- HEXAGONAL_RULES.yaml: Needs clarity on layer responsibilities
- DDD_RULES.yaml: Needs clarity on application layer structure
- Library module: Needs refactored application/ layer

---

## Decision

We adopt a **clean, segregated layer architecture** at `backend/api/app/` level:

### 1. **Directory Structure** (Approved)

```
backend/api/
├── dependencies.py              ← DI Container (global)
│   ├── get_db_session()
│   ├── get_current_user_id()
│   ├── get_create_library_use_case()
│   └── ... (41 UseCase factory methods)
│
└── app/
    ├── __init__.py
    ├── main.py                  ← FastAPI app entry point
    ├── conftest.py              ← pytest fixtures (App level)
    │
    ├── config/                  ← ✅ NEW: Configuration Layer
    │   ├── __init__.py
    │   ├── database.py          ← SQLAlchemy Base
    │   ├── security.py          ← Auth helpers
    │   ├── settings.py          ← Pydantic Settings (env vars)
    │   └── logging_config.py    ← Logging setup
    │
    ├── core/                    ← ✅ REFINED: Core Infrastructure
    │   └── __init__.py
    │       └── exceptions.py    ← System-level exceptions only
    │
    ├── shared/                  ← ✅ ENHANCED: Cross-Module Code
    │   ├── __init__.py
    │   ├── base.py              ← DDD base classes
    │   ├── errors.py            ← Business exceptions
    │   ├── events.py            ← Event base class
    │   ├── schemas.py           ← Shared Pydantic models
    │   └── deps.py              ← Common dependencies
    │
    ├── modules/                 ← ✅ PRESERVED: Domain Modules
    │   ├── library/
    │   │   ├── domain/
    │   │   ├── application/
    │   │   ├── routers/
    │   │   └── ...
    │   ├── bookshelf/
    │   ├── book/
    │   ├── block/
    │   ├── tag/
    │   └── media/
    │
    └── tests/                   ← ✅ PRESERVED: Integration Tests
        ├── conftest.py          ← Tests-level fixtures
        ├── test_integration_*.py
        └── test_*/
```

### 2. **Layer Responsibilities**

| Layer | Location | Purpose | Constraint |
|-------|----------|---------|------------|
| **Config** | `app/config/` | Application configuration (DB, Security, Settings) | Pure configuration, no business logic |
| **Core** | `app/core/` | System-level exceptions, infrastructure basics | No domain logic |
| **Shared** | `app/shared/` | Cross-module reusable code (base classes, exceptions, deps) | No module-specific logic |
| **Modules** | `app/modules/*/` | Domain logic (domain/, application/, routers/) | Self-contained per module |
| **Tests** | `app/tests/` | Integration tests, fixtures | pytest fixtures at App level |
| **DI** | `api/dependencies.py` | Global DI container (factories, composition root) | Centralized factory methods |
| **Main** | `app/main.py` | FastAPI app setup | FastAPI initialization + route registration |

### 3. **File Movements**

| Current | New | Reason |
|---------|-----|--------|
| `app/core/database.py` | `app/config/database.py` | Clear semantics: "config" layer |
| `app/core/security.py` | `app/config/security.py` | Clear semantics: "config" layer |
| `app/config.py` (if Pydantic Settings) | `app/config/settings.py` | Consolidate all config in `config/` folder |
| `app/infra/` | **DELETE** | Duplicate of `backend/infra/` |
| `app/core/__init__.py` | `app/core/__init__.py` (refined) | Only system exceptions |

### 4. **Deletion: `backend/api/app/infra/`**

**Files to delete:**
```
❌ app/infra/event_bus.py          (duplicate of backend/infra/event_bus/)
❌ app/infra/event_handler_registry.py (duplicate of backend/infra/event_bus/handlers/)
❌ app/infra/cache.py              (empty, unused)
❌ app/infra/database.py           (empty, unused)
❌ app/infra/logger.py             (empty, unused)
❌ app/infra/storage.py            (empty, unused)
❌ app/infra/__init__.py           (empty, delete folder)
```

**Reasoning:**
- `backend/infra/` is the true infrastructure layer (Hexagonal pattern)
- `app/infra/` is leftover transition code from previous refactor
- All imports should point to `backend/infra/` instead

### 5. **Hexagonal Architecture Alignment**

```
Hexagonal Layers (from HEXAGONAL_RULES.yaml):

┌─ Domain Layer (app/modules/*/domain/)
│   └─ Pure business logic, zero dependencies
│
├─ Application Layer (app/modules/*/application/)
│   ├─ ports/input.py (UseCase interfaces)
│   ├─ ports/output.py (Repository interfaces)
│   └─ use_cases/ (UseCase implementations)
│
├─ HTTP Adapter (app/modules/*/routers/)
│   └─ FastAPI routes (HTTP to UseCase bridge)
│
├─ Shared Layer (app/shared/)
│   ├─ base.py (AggregateRoot, Entity, ValueObject)
│   ├─ errors.py (Business exceptions)
│   ├─ events.py (DomainEvent base class)
│   └─ deps.py (Common FastAPI dependencies)
│
├─ Config Layer (app/config/)
│   ├─ database.py (SQLAlchemy setup)
│   ├─ security.py (Auth helpers)
│   └─ settings.py (Environment variables)
│
├─ Core Layer (app/core/)
│   └─ exceptions.py (System errors: SystemError, DatabaseError)
│
├─ Infrastructure (backend/infra/)
│   ├─ database/models/ (ORM Models)
│   ├─ storage/ (Repository implementations)
│   └─ event_bus/ (EventBus adapter)
│
└─ DI Container (api/dependencies.py)
    └─ Factory methods for all use cases + repositories
```

---

## Rationale

### Why separate `config/` from `core/`?

**Config Layer (`app/config/`)**:
- Contains application configuration
- Can change between environments (dev/test/prod)
- Examples: DATABASE_URL, JWT_SECRET_KEY, LOGGING_LEVEL
- **Semantic clarity**: "config" clearly means configuration

**Core Layer (`app/core/`)**:
- Contains system-level infrastructure exceptions
- Does not change between environments
- Examples: SystemError, DatabaseError, ConfigurationError
- **Semantic clarity**: "core" means foundational, immutable

### Why delete `app/infra/`?

**Hexagonal Architecture Rule**: Each layer should have ONE clear location

- ✅ Infrastructure adapters belong in `backend/infra/`
- ❌ `app/infra/` duplicates this and confuses dependency flow
- Imports should be: `from infra.storage import LibraryRepositoryImpl`
- NOT: `from app.infra.storage import ...` (which doesn't exist)

### Why enhance `app/shared/`?

**Cross-module reusability**:
- `base.py`: AggregateRoot, Entity, ValueObject (DDD)
- `errors.py`: Business exceptions (domain-level, not HTTP)
- `events.py`: DomainEvent base class
- `schemas.py`: Pydantic models (RequestBody, ResponseBody DTOs)
- `deps.py`: FastAPI Depends() helpers (get_db_session, get_current_user, etc.)

---

## Implementation Plan

### Phase 1: Create & Move Files (Today)

```bash
# 1. Create config/ structure
mkdir -p backend/api/app/config
mv backend/api/app/core/database.py backend/api/app/config/
mv backend/api/app/core/security.py backend/api/app/config/

# 2. Create config/__init__.py
# 3. Create config/settings.py
# 4. Create config/logging_config.py

# 5. Enhance core/__init__.py (only exceptions)
# 6. Enhance shared/ (base.py exists, fill in errors.py, events.py, deps.py)

# 7. Delete infra/
rm -rf backend/api/app/infra/
```

### Phase 2: Update Imports (Today)

```python
# ❌ OLD
from api.app.core.database import Base
from api.app.core.security import get_test_user_id

# ✅ NEW
from api.app.config import Base, get_test_user_id
# or
from api.app.config.database import Base
from api.app.config.security import get_test_user_id
```

**Affected files** (use grep to find all):
```bash
grep -r "from.*core.*database" backend/api/
grep -r "from.*core.*security" backend/api/
grep -r "from.*app.*infra" backend/api/
```

### Phase 3: Module Library Refactor (Today)

Following this ADR, refactor `library` module:

```
backend/api/app/modules/library/
├── domain/                      ← NEW: Split from domain.py
│   ├── __init__.py
│   ├── library.py              ← AggregateRoot
│   ├── library_name.py         ← ValueObject
│   └── events.py               ← DomainEvents
│
├── application/                 ← NEW: Complete structure
│   ├── __init__.py
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── input.py            ← UseCase interfaces + DTOs
│   │   └── output.py           ← Repository interface
│   └── use_cases/
│       ├── __init__.py
│       ├── create_library.py
│       ├── get_library.py
│       └── delete_library.py
│
├── routers/                     ← NEW: HTTP adapter
│   ├── __init__.py
│   └── library_router.py       ← FastAPI routes
│
├── exceptions.py               ← Business exceptions (KEEP)
├── schemas.py                  ← Pydantic DTOs (KEEP)
├── models.py                   ← ORM Model (move to infra later)
├── conftest.py                 ← pytest fixtures (KEEP)
└── __init__.py                 ← Public interface (REFACTOR)
```

---

## Consequences

### Benefits ✅

1. **Clear semantic organization**
   - `config/` → configuration
   - `core/` → system infrastructure
   - `shared/` → cross-module
   - `modules/` → domain logic

2. **Removes duplication**
   - Single source of truth: `backend/infra/`
   - Eliminates confusion: no more `app/infra/`

3. **Enables Hexagonal Architecture strictly**
   - Dependencies flow inward (Domain ← App ← Infra)
   - No circular dependencies

4. **Easier onboarding**
   - New developers see clear layer purposes
   - Less guesswork about where code goes

### Risks ⚠️

1. **Import path changes**
   - All references to `core.database` → `config.database`
   - Mitigation: Use IDE refactor tool (one-pass change)

2. **Deletion of `app/infra/`**
   - If any code depends on `app/infra.event_bus`, it will break
   - Mitigation: Pre-check with grep (see Phase 2)

3. **Temporary inconsistency**
   - While refactoring, some modules old structure, some new
   - Mitigation: Complete library module first, then other 5 modules

---

## Related Documents

| Document | Reference | Purpose |
|----------|-----------|---------|
| HEXAGONAL_RULES.yaml | Part 1: Ports & Adapters | Architecture rules |
| DDD_RULES.yaml | library domain spec | Business rules for library |
| ADR-027 | System Rules Consolidation | Previous architecture decision |
| ADR-001 to ADR-026 | Various ADRs | Historical context |

---

## Migration Checklist

- [ ] Create `app/config/` directory structure
- [ ] Move `database.py` and `security.py` to `config/`
- [ ] Create `config/settings.py` (Pydantic Settings)
- [ ] Create `config/__init__.py` (exports)
- [ ] Refine `core/__init__.py` (only exceptions)
- [ ] Enhance `shared/` (errors.py, events.py, deps.py, schemas.py)
- [ ] Update all imports across `backend/api/`
- [ ] Delete `app/infra/` folder
- [ ] Refactor `library` module (domain/ + application/)
- [ ] Refactor remaining 5 modules (bookshelf, book, block, tag, media)
- [ ] Run tests: `pytest backend/api/app/tests/ -v`
- [ ] Update documentation in module __init__.py files

---

## Approval

- **Decided By**: Architecture Team
- **Date**: 2025-11-13
- **Status**: ✅ APPROVED & IN PROGRESS
- **Next Review**: After Phase 3 completion (all 6 modules refactored)

---

## Related ADRs

- **ADR-027**: System Rules Consolidation (foundation for this decision)
- **ADR-008 to ADR-011**: Service & Repository Design per module
- **ADR-018 to ADR-026**: API maturity and implementation details

---

## Appendix A: File Comparison

### Before (Confusing)

```
app/
├── core/
│   ├── database.py       ← Configuration?
│   └── security.py       ← Configuration?
├── infra/
│   ├── event_bus.py      ← Duplicate!
│   └── event_handler_registry.py ← Duplicate!
└── shared/
    ├── base.py           ← Good
    └── (errors.py missing)
    └── (deps.py missing)
```

### After (Clear)

```
app/
├── config/
│   ├── database.py       ← ✅ Clear: Configuration
│   ├── security.py       ← ✅ Clear: Configuration
│   ├── settings.py       ← ✅ New: Environment variables
│   └── logging_config.py ← ✅ New: Logging setup
├── core/
│   └── exceptions.py      ← ✅ System-level only
├── shared/
│   ├── base.py            ← ✅ DDD base classes
│   ├── errors.py          ← ✅ Business exceptions
│   ├── events.py          ← ✅ Event base class
│   ├── schemas.py         ← ✅ Shared Pydantic models
│   └── deps.py            ← ✅ FastAPI dependencies
└── (NO infra/ folder!)    ← ✅ Deleted (duplicate)
```

---

## Appendix B: Hexagonal Mapping

| HEXAGONAL_RULES Reference | Implementation | File Location |
|---------------------------|-----------------|-----------------|
| Inbound Ports | REST API (FastAPI) | `modules/*/routers/*.py` |
| Outbound Ports | Repository interfaces | `modules/*/application/ports/output.py` |
| Input Ports | UseCase interfaces + DTOs | `modules/*/application/ports/input.py` |
| Domain Layer | Pure business logic | `modules/*/domain/` |
| Application Layer | UseCases | `modules/*/application/use_cases/` |
| Config Layer | ✅ **NEW** This ADR | `app/config/` |
| Infrastructure | ORM, EventBus, storage | `backend/infra/` |
| DI Container | Factories, composition root | `api/dependencies.py` |

---

## Appendix C: Library Module Structure (Example)

After this ADR, library module will look like:

```
modules/library/
├── domain/                          ← Step 1: Refactor
│   ├── __init__.py                 ← Exports: Library, LibraryName, ...events
│   ├── library.py                  ← AggregateRoot
│   ├── library_name.py             ← ValueObject
│   └── events.py                   ← DomainEvents
│
├── application/                     ← Step 2: This ADR
│   ├── __init__.py                 ← Exports: all UseCase interfaces + implementations
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── input.py                ← 4 UseCase ABCs (Create, Get, Delete, Rename)
│   │   └── output.py               ← ILibraryRepository interface
│   │
│   └── use_cases/
│       ├── __init__.py
│       ├── create_library.py       ← CreateLibraryUseCase
│       ├── get_library.py          ← GetLibraryUseCase
│       └── delete_library.py       ← DeleteLibraryUseCase
│
├── routers/                         ← Step 3: HTTP Adapter (next)
│   ├── __init__.py
│   └── library_router.py           ← 2 endpoints: POST /libraries, GET /libraries/{id}
│
├── exceptions.py                   ← Domain exceptions (unchanged)
├── schemas.py                      ← Pydantic DTOs (unchanged)
├── models.py                       ← ORM Model (will move to infra/database/models/)
├── conftest.py                     ← pytest fixtures (unchanged)
└── __init__.py                     ← Public module interface
```

Cross-References within library module:
```
domain/library.py
  ├─ imports: shared.base (AggregateRoot, DomainEvent)
  └─ imports: .library_name (ValueObject)

application/use_cases/create_library.py
  ├─ imports: domain.Library (Domain factory)
  ├─ imports: ports.input (ICreateLibraryUseCase, CreateLibraryRequest/Response)
  └─ imports: ports.output (ILibraryRepository)

routers/library_router.py
  ├─ imports: application (CreateLibraryUseCase implementations from DI)
  └─ imports: schemas (Pydantic request/response models)

__init__.py
  ├─ exports: public domain objects (Library, LibraryName, ...events)
  └─ no internal implementation details exposed
```

---

**End of ADR-028**
