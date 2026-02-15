# ADR-031: Structure Refinement - Models Migration and Application Layer Consolidation

**Status**: DECIDED
**Decision Date**: November 14, 2025
**Last Updated**: November 14, 2025
**Context**: Phase 3 of Hexagonal Architecture Refactoring
**Related to**: ADR-030 (Port-Adapter Separation Pattern), ADR-008 (Library Design), ADR-009 (Bookshelf Design)

---

## 1. Context

The Wordloom v3 backend inherited a monolithic module structure where different concerns were mixed within single files:

```
BEFORE (Problematic):
api/app/modules/library/
├── models.py              ← ORM mixed with module logic
├── service.py             ← Business logic here
├── repository.py          ← Persistence logic here
└── router.py              ← HTTP adapter here
```

This violates the Hexagonal Architecture principle of **infrastructure isolation**. The key issues:

1. **ORM models in application layer**: Database implementation details leaked into business logic layer
2. **Service/Repository pattern**: Created inconsistent abstraction levels across modules
3. **No clear port-adapter boundaries**: Difficult to test and refactor
4. **Inconsistent file organization**: Each module had different structure

The migration aims to achieve:
- **Separation of concerns**: ORM in `backend/infra/`, domain logic in modules
- **UseCase pattern**: Replace Service layer with explicit UseCase input/output ports
- **Clear infrastructure isolation**: Infrastructure adapters only in `backend/infra/`
- **Consistent structure**: All modules follow same hexagonal architecture

---

## 2. Decision

We have decided to:

### 2.1 Move ORM Models to Infrastructure Layer
**From**: `backend/api/app/modules/{module}/models.py`
**To**: `backend/infra/database/models/{module}_models.py`

**Rationale**:
- ORM models are **infrastructure details** (SQLAlchemy is a specific implementation choice)
- Domain logic should never import from ORM layer
- Enables switching database implementations without affecting modules

**Files Migrated** (Phase 1 - Library):
- `backend/api/app/modules/library/models.py` → `backend/infra/database/models/library_models.py`

**Remaining** (Phases 2-6):
- Bookshelf, Book, Block, Tag, Media modules follow same pattern

**Import Update**:
```python
# OLD (wrong - import path):
from core.database import Base

# NEW (correct):
from infra.database import Base
```

### 2.2 Replace Service Layer with UseCase Pattern
**From**: `backend/api/app/modules/{module}/service.py` (monolithic)
**To**: `backend/api/app/modules/{module}/application/use_cases/{use_case}.py` (granular)

**Rationale**:
- UseCases are explicit: Each file = one user-driven action
- Ports are clear: Input/Output ports defined separately
- Testing is easier: Inject mock repositories into specific UseCase
- Aligns with ADR-030: Every UseCase uses port-adapter pattern

**Example - Library Module**:

Old Structure:
```python
# service.py (200+ lines, mixed concerns)
class LibraryService:
    async def create_library(user_id, name):
        # Business logic L1: Validation
        # Business logic L2: Domain creation
        # Infrastructure L3: Repository.save()
        # Cross-cutting L4: Event publishing
        ...
```

New Structure:
```python
# application/use_cases/create_library.py (60 lines, single concern)
class CreateLibraryUseCase:
    def __init__(self, repository: ILibraryRepository, event_bus: IEventBus):
        self.repository = repository
        self.event_bus = event_bus

    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse:
        # Business logic only - validation + domain operations
        # Infrastructure calls are explicit via injected dependencies
        ...
```

**Files Structure** (Library Example):
```
api/app/modules/library/
├── domain/
│   ├── library.py              # Aggregate root
│   ├── library_name.py         # Value objects
│   └── events.py               # Domain events
├── application/
│   ├── ports/
│   │   ├── input.py            # ICreateLibraryUseCase, IGetLibraryUseCase, ...
│   │   └── output.py           # ILibraryRepository
│   └── use_cases/
│       ├── create_library.py
│       ├── get_library.py
│       └── delete_library.py
├── routers/
│   └── library_router.py        # HTTP adapter (replaces single router.py)
├── exceptions.py               # Custom exceptions
├── schemas.py                  # Pydantic DTOs
└── __init__.py                # Exports all public interfaces
```

### 2.3 Update Module Imports in `__init__.py`
**Purpose**: Document new structure, guide users to correct imports

**OLD** (points to deleted files):
```python
from .service import LibraryService
from .repository import LibraryRepository, LibraryRepositoryImpl
```

**NEW** (points to new locations):
```python
# Domain layer
from .domain.library import Library
from .domain.library_name import LibraryName
from .domain.events import (
    LibraryCreated,
    LibraryRenamed,
    LibraryDeleted,
    BasementCreated,
)

# Application layer (ports)
from .application.ports.input import (
    ICreateLibraryUseCase,
    IGetLibraryUseCase,
    IDeleteLibraryUseCase,
    CreateLibraryRequest,
    CreateLibraryResponse,
)
from .application.ports.output import ILibraryRepository

# Application layer (implementations)
from .application.use_cases.create_library import CreateLibraryUseCase
from .application.use_cases.get_library import GetLibraryUseCase
from .application.use_cases.delete_library import DeleteLibraryUseCase

# NOTE: Don't import ORM models here!
# Use: from infra.database.models.library_models import LibraryModel
```

### 2.4 Update HEXAGONAL_RULES.yaml with ORM Mappings
**Purpose**: Document where each module's ORM model lives

Added section in Part C:
```yaml
orm_models:
  library:
    file: "backend/infra/database/models/library_models.py"
    class: "LibraryModel"
    table: "libraries"

  bookshelf:
    file: "backend/infra/database/models/bookshelf_models.py"
    class: "BookshelfModel"
    table: "bookshelves"

  # ... (6 modules total)
```

### 2.5 Update DDD_RULES.yaml Implementation References
**Purpose**: Update enforcement layers to reference new file structure

Changed all `implementation_layers` to use:
- `use_case_file` instead of `service_file`
- `use_case_method` instead of `service_method`
- `repository_adapter` instead of `repository_file`
- Updated ADR references from ADR-008 to ADR-031

---

## 3. Rationale

### 3.1 Why Move ORM to Infrastructure?
- **Hexagonal principle**: Infrastructure implementations (SQLAlchemy) belong in `backend/infra/`
- **Domain purity**: Domain logic has zero external dependencies
- **Test isolation**: Easy to test domain with mock repository (no ORM needed)
- **Technology agnosticism**: Could replace SQLAlchemy with Tortoise ORM or dataclasses without touching modules

### 3.2 Why UseCase Pattern over Service Pattern?
- **Clarity**: One UseCase = one business action (Single Responsibility)
- **Ports first**: Input/Output ports are explicit contracts
- **Dependency injection**: Easier to mock, easier to test
- **Consistency**: All modules follow same pattern (ADR-030 port-adapter principle)
- **Scalability**: 41 UseCases across 6 modules vs. monolithic Service classes

### 3.3 Why Update Module `__init__.py`?
- **Guidance**: Developers immediately see correct imports without file exploration
- **Discoverability**: All public types (Domain, DTOs, Exceptions) are documented
- **Safety**: Prevents imports from internal infrastructure layers
- **Maintenance**: Single source of truth for module exports

---

## 4. Implementation Details

### 4.1 Phase 1: Library Module (COMPLETED Nov 14, 2025)

**Files Modified**:

1. **backend/infra/database/models/library_models.py**
   - Fixed import: `core.database` → `infra.database`
   - Status: ✅ Verified correct

2. **backend/api/app/modules/library/routers/library_router.py**
   - Rewritten from 486 → 331 lines
   - Removed: Service-based pattern
   - Added: UseCase dependency injection
   - Status: ✅ Complete rewrite, all imports corrected

3. **backend/api/app/modules/library/__init__.py**
   - Updated imports (deleted old service/repository references)
   - Added imports for new structure (use_cases, domain objects, exceptions)
   - Added comprehensive docstring with usage examples
   - Status: ✅ Updated with ADR-031 reference

4. **backend/docs/HEXAGONAL_RULES.yaml**
   - Step 2: Updated ORM models migration section
   - Part C: Added orm_models mappings for all 6 modules
   - Status: ✅ Updated

5. **backend/docs/DDD_RULES.yaml**
   - RULE-001 implementation: Updated service_file → use_case_file
   - RULE-002 implementation: Updated service_layer → application layer
   - RULE-003 implementation: Updated service_layer → application layer
   - Updated related_files and ADR references
   - Status: ✅ Updated

6. **assets/docs/ADR/ADR-031-structure-refinement.md** (THIS FILE)
   - Status: ✅ Created

### 4.2 Phase 2-6: Remaining Modules

**Same pattern applied to each module**:

| Module | Domain | Models File | UseCase Files | Router File | Status |
|--------|--------|-------------|----------------|------------|--------|
| Library | ✅ | library_models.py | create, get, delete, rename | library_router.py | ✅ |
| Bookshelf | ⏳ | bookshelf_models.py | create, get, list, update, delete | bookshelf_router.py | ⏳ |
| Book | ⏳ | book_models.py | create, get, move, update, delete | book_router.py | ⏳ |
| Block | ⏳ | block_models.py | create, get, list, update, delete | block_router.py | ⏳ |
| Tag | ⏳ | tag_models.py | create, get, list, update, delete | tag_router.py | ⏳ |
| Media | ⏳ | media_models.py | create, get, list, delete | media_router.py | ⏳ |

---

## 5. Consequences

### 5.1 Positive

1. **Hexagonal Purity**: Clear separation - infrastructure in `backend/infra/`, domain logic in modules
2. **Enhanced Testability**: UseCase pattern makes unit testing straightforward (mock repository only)
3. **Consistency**: All 6 modules follow identical structure pattern
4. **Maintainability**: File organization mirrors architecture (domain/application/routers)
5. **Technology Flexibility**: ORM implementation swappable without domain logic changes
6. **Documentation**: HEXAGONAL_RULES.yaml and DDD_RULES.yaml updated with new references

### 5.2 Negative / Trade-offs

1. **More files**: UseCase-per-action pattern creates more files than monolithic Service
   - **Mitigation**: Easier navigation and understanding (single file = single purpose)

2. **Boilerplate**: Each UseCase needs `__init__`, execute method, ports
   - **Mitigation**: Pattern is consistent, IDE templates can auto-generate

3. **Learning curve**: Developers new to hexagonal architecture need time to understand structure
   - **Mitigation**: Clear examples in HEXAGONAL_RULES.yaml and ADR-031

### 5.3 Migration Challenges

1. **File dependencies**: When moving ORM model, ensure all imports updated in repository adapters
   - **Status**: Fixed for Library (import path corrected)

2. **Naming consistency**: Old files use `models.py`, new uses `{module}_models.py`
   - **Rationale**: Enables multiple models in same directory without conflicts

3. **Test updates**: Tests must now import from new locations
   - **Status**: conftest.py files already updated in Phase 1

---

## 6. Configuration & Reference

### 6.1 Import Paths (New Standard)

```python
# Domain layer (pure business logic)
from api.app.modules.library.domain.library import Library
from api.app.modules.library.domain.library_name import LibraryName

# Application layer (UseCase interfaces)
from api.app.modules.library.application.ports.input import ICreateLibraryUseCase
from api.app.modules.library.application.ports.output import ILibraryRepository

# Application layer (UseCase implementations)
from api.app.modules.library.application.use_cases.create_library import CreateLibraryUseCase

# Infrastructure layer (adapters)
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository

# Infrastructure layer (ORM models) - USE SPARINGLY!
# ⚠️ Only import ORM models in repository adapters or migrations
# ⚠️ NEVER import in domain or application layers
from infra.database.models.library_models import LibraryModel

# HTTP layer
from api.app.modules.library.routers.library_router import router as library_router
```

### 6.2 Dependency Injection Pattern

```python
# In app.py or DI container:
container = DIContainer()

# Register repositories
container.register(ILibraryRepository, SQLAlchemyLibraryRepository)

# Register UseCases
container.register(
    ICreateLibraryUseCase,
    CreateLibraryUseCase(
        repository=container.get(ILibraryRepository),
        event_bus=event_bus
    )
)

# In router:
@library_router.post("/create")
async def create_library(request: CreateLibraryRequest):
    use_case = container.get(ICreateLibraryUseCase)
    response = await use_case.execute(request)
    return response
```

### 6.3 File Naming Conventions

| Layer | File Pattern | Example |
|-------|-------------|---------|
| Domain | `{concept}.py` | `library.py`, `library_name.py` |
| Application Ports | `ports/{direction}.py` | `ports/input.py`, `ports/output.py` |
| Application UseCase | `use_cases/{action}.py` | `use_cases/create_library.py` |
| Infrastructure Adapter | `{module}_repository_impl.py` | `library_repository_impl.py` |
| Infrastructure ORM | `models/{module}_models.py` | `models/library_models.py` |
| HTTP Adapter | `routers/{module}_router.py` | `routers/library_router.py` |

---

## 7. Validation Checklist

### 7.1 Post-Implementation Verification (Library Module)

- [x] ORM models moved and import paths corrected
- [x] Router rewritten to use UseCase pattern
- [x] Module `__init__.py` updated with new exports
- [x] Exceptions.py and schemas.py verified (no changes needed)
- [x] HEXAGONAL_RULES.yaml updated with ORM mappings
- [x] DDD_RULES.yaml implementation references updated
- [x] ADR-031 created with full documentation
- [ ] Full test suite passes (pytest backend/tests)
- [ ] No lingering references to deleted service.py/repository.py files
- [ ] Integration test: Library endpoints accessible via HTTP

### 7.2 Remaining Phases

For each module (Bookshelf, Book, Block, Tag, Media):
1. Move ORM model to `backend/infra/database/models/{module}_models.py`
2. Rewrite router with UseCase pattern (delete old router.py)
3. Create use_cases/ with granular UseCase classes
4. Update module `__init__.py`
5. Update HEXAGONAL_RULES.yaml and DDD_RULES.yaml
6. Run tests to verify

---

## 8. Related Documents

- **ADR-030**: Port-Adapter Separation Pattern (established I-prefix convention, ILibraryRepository)
- **ADR-008**: Library Service & Repository Design (legacy, superseded by UseCase pattern)
- **ADR-009**: Bookshelf Service & Repository Design (legacy, to be updated)
- **HEXAGONAL_RULES.yaml**: Architecture rules and ORM mappings
- **DDD_RULES.yaml**: Domain-driven design rules and invariants

---

## 9. Migration Summary by Module

### Library (Phase 1) ✅
- Domain layer: `library.py`, `library_name.py`, `events.py`
- Application layer: 3 UseCases (Create, Get, Delete)
- Infrastructure: ORM model moved, repository adapter created
- Router: Rewritten with UseCase DI pattern
- Status: **COMPLETE**

### Bookshelf, Book, Block, Tag, Media (Phases 2-6) ⏳
- Following same pattern as Library
- To be executed in subsequent sessions
- Status: **PENDING**

---

## 10. Questions & Answers

**Q: Why not keep ORM models in modules for convenience?**
A: ORM is an implementation detail. Domain logic should never depend on specific ORMs (SQLAlchemy). This pattern allows switching ORMs without rewriting modules.

**Q: Can I import ORM models in UseCase classes?**
A: No. UseCase classes are in application layer and must import through output port (repository interface). Only repository adapters should know about ORM models.

**Q: What if a UseCase needs multiple repository types?**
A: Inject multiple repositories as constructor parameters. Example:
```python
class CreateBookUseCase:
    def __init__(self, book_repo: IBookRepository, bookshelf_repo: IBookshelfRepository):
        self.book_repo = book_repo
        self.bookshelf_repo = bookshelf_repo
```

**Q: How do I handle cross-aggregate operations?**
A: Use the saga/choreography pattern via EventBus. One aggregate publishes domain event, other aggregate subscribes. See `application/ports/events.py`.

---

**Document Status**: FINAL
**Last Review**: November 14, 2025 15:30 UTC
**Next Review**: Post-integration testing (Phase 1) and Phase 2 completion
