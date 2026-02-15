# ADR-030: Port-Adapter Separation Naming Convention

**Status**: DECIDED ✅
**Date**: 2025-11-14
**Deciders**: Architecture Team
**Related Documents**:
- ADR-029: API App Layer Architecture (foundation for this decision)
- HEXAGONAL_RULES.yaml (Part 1: Ports & Adapters, Part C: Port ↔ Adapter Mappings)
- DDD_RULES.yaml (library domain specification with new application layer)

---

## Context

After implementing Hexagonal Architecture across 6 modules (Step 8 complete), we discovered confusion around **naming conventions** for port interfaces vs. adapter implementations:

### The Problem

**Before (Confusing)**:
```python
# backend/api/app/modules/library/repository.py
class LibraryRepository(ABC):  # Is this a port interface or adapter?
    """Which file is the real implementation?"""

# backend/infra/storage/library_repository_impl.py
class LibraryRepositoryImpl:  # Is this the port? Or an adapter?
    """Or is this the real implementation?"""
```

**Questions This Raised**:
- What does `LibraryRepository` refer to? (Interface? Implementation? Adapter?)
- Where is the port interface really defined?
- How do developers know which class implements which interface?
- Will this scale to 41 UseCase abstractions?

### Design Principles Violated

1. **Interface Segregation**: Can't tell interface from implementation by name alone
2. **Naming Clarity**: Generic names don't convey architecture intent
3. **Technology Neutrality**: `Impl` suffix is too generic (Impl of what?)
4. **Scalability**: Without clear naming, adding 41 UseCase abstractions becomes chaotic

---

## Decision

**Adopt strict naming conventions to distinguish Port Interfaces from Adapter Implementations**:

### Rule 1: Port Interfaces Use `I` Prefix

```python
# backend/api/app/modules/{module}/application/ports/output.py
class ILibraryRepository(ABC):
    """Port Interface - contract for data persistence"""
    @abstractmethod
    async def save(self, library: Library) -> None: ...

class ICreateLibraryUseCase(ABC):
    """Port Interface - contract for create use case"""
    @abstractmethod
    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse: ...
```

**Rationale**:
- `I` prefix is industry standard for interfaces (C#, Java, TypeScript conventions)
- Immediately visible: `IXxx` = port, `Xxx` = adapter
- Unambiguous in code: `from ports.output import ILibraryRepository`

### Rule 2: Adapter Implementations Use Technology Prefix

**For Repository Adapters**:
```python
# backend/infra/storage/library_repository_impl.py
class SQLAlchemyLibraryRepository(ILibraryRepository):
    """Adapter Implementation - SQLAlchemy ORM implementation"""
    def __init__(self, session: Session): ...

    async def save(self, library: Library) -> None: ...
```

**Rationale**:
- `SQLAlchemy` prefix clarifies: "This is the SQLAlchemy implementation"
- Enables future alternatives: `PostgresLibraryRepository`, `MongoLibraryRepository`, etc.
- No `Impl` suffix - the technology is the implementation detail

**For UseCase Adapters**:
```python
# backend/api/app/modules/library/application/use_cases/create_library.py
class CreateLibraryUseCase(ICreateLibraryUseCase):
    """Adapter Implementation - primary use case implementation"""
    def __init__(self, repository: ILibraryRepository, eventbus: IEventBus): ...

    async def execute(self, request: CreateLibraryRequest) -> CreateLibraryResponse: ...
```

**Rationale**:
- No technology prefix needed (uses cases are architecture-neutral)
- Class name matches the action: `CreateLibraryUseCase` implements `ICreateLibraryUseCase`
- Simple pattern: `I{Name}UseCase` (interface) → `{Name}UseCase` (implementation)

### Rule 3: Consistent Dependency Declaration

```python
# ✅ Correct: Always depend on Interfaces (I-prefix)
def __init__(self, repository: ILibraryRepository, eventbus: IEventBus):
    self.repository = repository  # Expects ILibraryRepository

# ❌ Wrong: Never depend on Implementations
def __init__(self, repository: SQLAlchemyLibraryRepository):
    self.repository = repository  # Too tightly coupled
```

**Rationale**:
- Port interfaces are stable (business contracts)
- Implementations can change (technology decisions)
- Dependencies flow inward (Domain ← App ← Infra)

---

## Rationale

### Why This Pattern Solves the Problem

| Issue | Solution |
|-------|----------|
| "Is this a port or adapter?" | `IXxx` = port, `Xxx` = adapter → immediately clear |
| "Where's the implementation?" | Look for `SQLAlchemy{X}` or `{X}UseCase` class |
| "What if I add mock adapters?" | `MockLibraryRepository(ILibraryRepository)` is obvious |
| "Scales to 41 use cases?" | Pattern is consistent across all 41: I + UseCase |
| "How do I find the port?" | Search for `IXxx` in ports/ directory |

### Naming Convention Summary

```
=== Repository Adapters ===

Port Interface:
  Location: backend/api/app/modules/{module}/application/ports/output.py
  Naming: I{Entity}Repository
  Example: ILibraryRepository, IBookshelfRepository

Adapter Implementation:
  Location: backend/infra/storage/{module}_repository_impl.py
  Naming: SQLAlchemy{Entity}Repository
  Example: SQLAlchemyLibraryRepository, SQLAlchemyBookshelfRepository

=== UseCase Adapters ===

Port Interfaces:
  Location: backend/api/app/modules/{module}/application/ports/input.py
  Naming: I{Action}{Entity}UseCase or I{Entity}{Action}UseCase
  Example: ICreateLibraryUseCase, IGetLibraryUseCase, IDeleteLibraryUseCase

Adapter Implementations:
  Location: backend/api/app/modules/{module}/application/use_cases/{action}_{entity}.py
  Naming: {Action}{Entity}UseCase
  Example: CreateLibraryUseCase, GetLibraryUseCase, DeleteLibraryUseCase
```

---

## Implementation

### Phase 1: Apply to Library Module ✅

**Status**: COMPLETE (Nov 14, 2025)

**Port Interfaces Created**:
```
backend/api/app/modules/library/application/ports/output.py
  ├─ ILibraryRepository

backend/api/app/modules/library/application/ports/input.py
  ├─ ICreateLibraryUseCase
  ├─ IGetLibraryUseCase
  ├─ IDeleteLibraryUseCase
  └─ IRenameLibraryUseCase
```

**Adapter Implementations Created**:
```
backend/infra/storage/library_repository_impl.py
  └─ SQLAlchemyLibraryRepository

backend/api/app/modules/library/application/use_cases/
  ├─ create_library.py (CreateLibraryUseCase)
  ├─ get_library.py (GetLibraryUseCase)
  └─ delete_library.py (DeleteLibraryUseCase)
```

**References Updated**:
- ✅ backend/api/dependencies.py: Uses `ILibraryRepository` for DI
- ✅ backend/infra/storage/library_repository_impl.py: Implements `ILibraryRepository`
- ✅ backend/api/app/tests/test_integration_four_modules.py: Imports `SQLAlchemyLibraryRepository`

### Phase 2: Apply to Other 5 Modules (Pending)

| Module | Port Interfaces | Adapter Classes |
|--------|---|---|
| Bookshelf | IBookshelfRepository + 4 UseCases | SQLAlchemyBookshelfRepository + 4 UseCases |
| Book | IBookRepository + 5 UseCases | SQLAlchemyBookRepository + 5 UseCases |
| Block | IBlockRepository + 6 UseCases | SQLAlchemyBlockRepository + 6 UseCases |
| Tag | ITagRepository + 10 UseCases | SQLAlchemyTagRepository + 10 UseCases |
| Media | IMediaRepository + 13 UseCases | SQLAlchemyMediaRepository + 13 UseCases |

---

## Mapping Table: All 6 Modules

### Library

| Type | Port Interface | Adapter Class | Port File | Adapter File |
|------|---|---|---|---|
| Repository | `ILibraryRepository` | `SQLAlchemyLibraryRepository` | `backend/api/app/modules/library/application/ports/output.py` | `backend/infra/storage/library_repository_impl.py` |
| UseCase | `ICreateLibraryUseCase` | `CreateLibraryUseCase` | `backend/api/app/modules/library/application/ports/input.py` | `backend/api/app/modules/library/application/use_cases/create_library.py` |
| UseCase | `IGetLibraryUseCase` | `GetLibraryUseCase` | `backend/api/app/modules/library/application/ports/input.py` | `backend/api/app/modules/library/application/use_cases/get_library.py` |
| UseCase | `IDeleteLibraryUseCase` | `DeleteLibraryUseCase` | `backend/api/app/modules/library/application/ports/input.py` | `backend/api/app/modules/library/application/use_cases/delete_library.py` |

### Bookshelf (Template)

| Type | Port Interface | Adapter Class | Port File | Adapter File |
|------|---|---|---|---|
| Repository | `IBookshelfRepository` | `SQLAlchemyBookshelfRepository` | `backend/api/app/modules/bookshelf/application/ports/output.py` | `backend/infra/storage/bookshelf_repository_impl.py` |
| UseCase | `ICreateBookshelfUseCase` | `CreateBookshelfUseCase` | `backend/api/app/modules/bookshelf/application/ports/input.py` | `backend/api/app/modules/bookshelf/application/use_cases/create_bookshelf.py` |
| ... | ... | ... | ... | ... |

### Book, Block, Tag, Media (Follow Same Pattern)

---

## Consequences

### Benefits ✅

1. **Immediate Clarity**: `IXxx` (interface) vs `Xxx` (adapter) - no ambiguity
2. **IDE Support**: IntelliSense shows `IXxx` = abstract, `Xxx` = concrete
3. **Test Mocking Easy**: `MockLibraryRepository(ILibraryRepository)` is obvious
4. **Scalable**: Works for 41 use cases without confusion
5. **Industry Standard**: Follows C#/.NET/TypeScript conventions
6. **Technology Agnostic**: `SQLAlchemyXxx` prefix is replaceable

### Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Breaking existing imports | Update 135+ files in bulk with IDE refactor tool |
| Developer learning curve | Document pattern in HEXAGONAL_RULES.yaml + ADR-030 |
| `I` prefix feels verbose | It's 1 character - benefit far outweighs cost |
| Future generators may create wrong names | Code review checklist: "All ports use I prefix?" |

---

## Related Decisions

| Decision | Impact | Link |
|----------|--------|------|
| ADR-029 | Defines app/config/core/shared layer structure | Foundation for this ADR |
| ADR-008 to ADR-026 | Service & Repository designs (old pattern) | Superseded by this ADR naming |
| HEXAGONAL_RULES.yaml Part C | Port ↔ Adapter mappings | Implementation guide |
| Step 3 to Step 8 | 8-step hexagonal conversion | Uses this naming from here forward |

---

## Migration Checklist

### Library Module ✅

- [x] Rename `LibraryRepository` → `ILibraryRepository` in ports/output.py
- [x] Rename `LibraryRepositoryImpl` → `SQLAlchemyLibraryRepository` in infra/storage/
- [x] Update all imports in dependencies.py to use `ILibraryRepository`
- [x] Update test file imports to use `SQLAlchemyLibraryRepository`
- [x] Create port interfaces `ICreateLibraryUseCase`, `IGetLibraryUseCase`, etc.
- [x] Rename use cases: `CreateLibraryUseCase` implements `ICreateLibraryUseCase`
- [x] Update HEXAGONAL_RULES.yaml with mapping table
- [x] Update DDD_RULES.yaml library layer structure

### Other 5 Modules (Pending)

- [ ] Apply same pattern to Bookshelf module
- [ ] Apply same pattern to Book module
- [ ] Apply same pattern to Block module
- [ ] Apply same pattern to Tag module (10 use cases)
- [ ] Apply same pattern to Media module (13 use cases)
- [ ] Bulk test file updates: all repository and use case imports
- [ ] Run full test suite to verify no breakage
- [ ] Update module __init__.py files to export correct names

---

## Documentation

**Where to Reference This Pattern**:

1. **New Developer Onboarding**:
   - Point to ADR-030 in architecture guide
   - Explain: `IXxx` = port, `Xxx` = adapter

2. **Code Review Checklist**:
   - Port interfaces must use `I` prefix
   - Repository adapters must use `SQLAlchemy` prefix
   - UseCase adapters use no prefix (just the action)

3. **Architectural Decision Records**:
   - ADR-029: App Layer (layer structure)
   - ADR-030: **Port-Adapter Separation** (this document - naming conventions)
   - ADR-031+: Specific module implementations

---

## Decision Log

| Date | Decision | Status |
|------|----------|--------|
| 2025-11-13 | Created library application layer (ports + use cases) | ✅ COMPLETE |
| 2025-11-13 | Discovered naming confusion: LibraryRepository vs LibraryRepositoryImpl | ⚠️ IDENTIFIED |
| 2025-11-14 | Defined I-prefix convention for port interfaces | ✅ DECIDED |
| 2025-11-14 | Defined SQLAlchemy-prefix for repository adapters | ✅ DECIDED |
| 2025-11-14 | Applied to library module and updated tests | ✅ IMPLEMENTED |
| 2025-11-14 | This ADR: Documented pattern for all modules | ✅ APPROVED |

---

## References

**Source Documents**:
- `backend/api/app/modules/library/application/ports/output.py` (ILibraryRepository)
- `backend/infra/storage/library_repository_impl.py` (SQLAlchemyLibraryRepository)
- `backend/api/app/modules/library/application/ports/input.py` (ICreateLibraryUseCase, etc.)
- `backend/api/app/modules/library/application/use_cases/*.py` (CreateLibraryUseCase, etc.)

**Related ADRs**:
- **ADR-029**: Application Layer Architecture (foundation)
- **ADR-027**: System Rules Consolidation
- **ADR-028**: System Rules Three-File Architecture
- **ADR-001**: Independent Aggregate Roots
- **ADR-008 to ADR-011**: Service & Repository Design (old pattern)
- **ADR-018 to ADR-026**: API Maturity

**External Standards**:
- C# Interface Naming: `IRepository` pattern (Microsoft.NET design guidelines)
- Java Interface Naming: `IRepository` pattern (Google Java Style Guide)
- TypeScript Interface Naming: `IRepository` pattern (official TypeScript handbook)

---

## Approval

- **Status**: ✅ DECIDED
- **Date**: 2025-11-14
- **Approved By**: Architecture Team
- **Implementation Date**: 2025-11-14 (Library module)
- **Rollout**: All 6 modules by 2025-11-15

---

## Appendix A: Quick Reference

### Port vs Adapter at a Glance

```
┌─ PORT (defines contract)
│  ├─ Location: backend/api/app/modules/{module}/application/ports/
│  ├─ Naming: I{Name}
│  └─ Example: ILibraryRepository, ICreateLibraryUseCase
│
└─ ADAPTER (implements contract)
   ├─ Repository Adapter
   │  ├─ Location: backend/infra/storage/
   │  ├─ Naming: SQLAlchemy{Name}Repository
   │  └─ Example: SQLAlchemyLibraryRepository
   │
   └─ UseCase Adapter
      ├─ Location: backend/api/app/modules/{module}/application/use_cases/
      ├─ Naming: {Action}{Name}UseCase
      └─ Example: CreateLibraryUseCase
```

### Import Statements

```python
# ✅ Correct: Import port interface
from api.app.modules.library.application.ports.output import ILibraryRepository
from infra.storage.library_repository_impl import SQLAlchemyLibraryRepository

# ✅ Correct: DI container wires implementation to port
@property
def get_library_repository(self) -> ILibraryRepository:
    return SQLAlchemyLibraryRepository(self.db_session)

# ✅ Correct: UseCase depends on port
class CreateLibraryUseCase(ICreateLibraryUseCase):
    def __init__(self, repository: ILibraryRepository):
        self.repository = repository

# ❌ Wrong: UseCase depends on adapter
class CreateLibraryUseCase(ICreateLibraryUseCase):
    def __init__(self, repository: SQLAlchemyLibraryRepository):  # Too tight coupling!
        self.repository = repository
```

---

**End of ADR-030**

