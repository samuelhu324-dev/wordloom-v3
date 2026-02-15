# ADR-031: Library Module Architecture Verification & Quality Gate

**Status**: ACCEPTED
**Decision Date**: November 14, 2025
**Last Updated**: November 14, 2025
**Context**: Phase 3 Library Module Refactoring - Post-Migration Validation
**Related ADRs**: ADR-030 (Port-Adapter Separation), ADR-012 (ORM Model Strategy)

---

## 1. Context

After completing Phase 1 of the Hexagonal Architecture migration for the Library module, we need to:

1. **Verify correctness** of migrated files and import paths
2. **Ensure consistency** with HEXAGONAL_RULES.yaml and DDD_RULES.yaml
3. **Establish quality gates** before scaling to remaining 5 modules (Bookshelf, Book, Block, Tag, Media)
4. **Document validation approach** for future phases

**Current State**:
- ✅ Library models migrated to `backend/infra/database/models/library_models.py`
- ✅ UseCase pattern implemented in router (`library_router.py`)
- ✅ Repository adapter created (`library_repository_impl.py`)
- ✅ HEXAGONAL_RULES.yaml and DDD_RULES.yaml updated with new paths
- ⏳ Static imports verification pending
- ⏳ Integration test baseline pending

---

## 2. Decision

We have decided to:

### 2.1 Implement Three-Level Validation Strategy

**P0 - Critical Path (File Correctness)**:
- Verify `library_models.py` imports `from infra.database import Base` (not `core.database`)
- Verify `library_repository_impl.py` implements `ILibraryRepository` interface
- Verify `library_router.py` only depends on UseCase classes (never directly accesses Repository)
- Verify import paths in `library/__init__.py` don't reference deleted service.py/repository.py files

**P1 - Documentation Consistency**:
- Update DDD_RULES.yaml: replace `backend/api/app/modules/library/models.py` → `backend/infra/database/models/library_models.py`
- Update HEXAGONAL_RULES.yaml: ensure ORM model mappings use `{module}_models.py` (plural) pattern
- Add naming conventions explicitly:
  - Port interfaces: `I{Entity}Repository`
  - Adapter implementations: `SQLAlchemy{Entity}Repository`
  - ORM models: `{module}_models.py` with base import from `infra.database.Base`

**P2 - Executable Verification**:
- Create `tools/verify_library.py` script for automated import checking
- Document how to run integration tests (once environment is ready)
- Generate this ADR-031 to codify validation approach

### 2.2 Validation Checklist for Each Module

For Library and all future modules (Bookshelf, Book, Block, Tag, Media), verify:

| Item | P0/P1/P2 | Verification | Status |
|------|----------|--------------|--------|
| ORM model import path | P0 | `grep "from infra.database import Base"` | ✅ |
| Repository implements port | P0 | `issubclass(SQLAlchemy{Entity}Repository, I{Entity}Repository)` | ✅ |
| Router uses only UseCase | P0 | No direct imports of `infra.storage.*` in router | ✅ |
| Module __init__.py clean | P0 | No deleted file references (service.py, old repository.py) | ✅ |
| DDD_RULES.yaml updated | P1 | ORM path → `backend/infra/database/models/{module}_models.py` | ✅ |
| HEXAGONAL_RULES.yaml sync | P1 | Port/adapter mappings document all 6 modules | ✅ |
| Naming conventions clear | P1 | I-prefix + SQLAlchemy prefix documented | ✅ |
| Import script passes | P2 | `tools/verify_library.py` reports all imports OK | ⏳ |
| Integration tests pass | P2 | Domain/Repository/Router integration tests green | ⏳ |

---

## 3. Rationale

### 3.1 Why Three-Level Validation?

1. **P0 (Critical)**: Catches architectural violations immediately (ORM leaks into domain, service pattern returns, etc.)
2. **P1 (Documentation)**: Ensures consistency across all 6 modules and future maintenance
3. **P2 (Executable)**: Automates checks to prevent regressions during scaling to other modules

### 3.2 Why Explicit Naming Conventions?

Current state has some ambiguity:
- Repository adapter naming could be misunderstood (is it `LibraryRepository` or `SQLAlchemyLibraryRepository`?)
- ORM model location was mixed (some still in modules/, now in infra/)
- Port interface naming wasn't uniformly applied (ILibraryRepository is good, but not all modules follow)

**Solution**: Explicit in HEXAGONAL_RULES.yaml:
```yaml
naming_conventions:
  port_interface: "I{Entity}Repository (I-prefix for interface contracts)"
  adapter_class: "SQLAlchemy{Entity}Repository (SQLAlchemy prefix for ORM implementation)"
  orm_models: "{module}_models.py (plural + _models), import from infra.database.Base"
```

This makes it unambiguous for all 6 modules and easier to auto-validate.

### 3.3 Why Executable Verification?

Manual checklist is error-prone at scale (6 modules × 5 checks × N developers).
A script (`tools/verify_library.py`) can:
- Check all 11 critical imports
- Verify interface implementations
- Detect naming violations
- Run in CI/CD pipeline

---

## 4. Implementation

### 4.1 Files Updated (This Decision)

1. **backend/docs/DDD_RULES.yaml**
   - Updated library.implementation_files: `models.py` → `backend/infra/database/models/library_models.py`

2. **backend/docs/HEXAGONAL_RULES.yaml**
   - Clarified naming conventions (I-prefix, SQLAlchemy prefix, _models.py pattern)
   - Verified ORM model mappings for all 6 modules

3. **tools/verify_library.py** (NEW)
   - Automated import verification script
   - Checks all 11 critical module imports
   - Verifies interface implementations (ILibraryRepository → SQLAlchemyLibraryRepository)
   - Detects class naming violations

### 4.2 Verification Results for Library

**P0 - File Correctness**: ✅ PASSED
```
✅ library_models.py imports from infra.database.Base
✅ library_repository_impl.py implements ILibraryRepository (issubclass check passes)
✅ library_router.py only imports UseCase classes, no direct Repository access
✅ library/__init__.py clean (no service.py or deleted repository.py references)
```

**P1 - Documentation Consistency**: ✅ PASSED
```
✅ DDD_RULES.yaml updated with infra/database/models path
✅ HEXAGONAL_RULES.yaml port/adapter mappings align
✅ Naming conventions explicit (I-prefix, SQLAlchemy-prefix, _models.py)
```

**P2 - Executable Verification**: ⏳ PENDING
```
⏳ tools/verify_library.py runs but requires PYTHONPATH setup (dependency on environment)
⏳ Integration tests require pytest + database setup (pending)
```

---

## 5. Consequences

### 5.1 Positive

1. **Quality Gate Established**: Prevents architectural regression in remaining 5 modules
2. **Automation Ready**: `tools/verify_library.py` can be incorporated into CI/CD
3. **Clear Contracts**: Naming conventions make it obvious what's a port vs. adapter
4. **Consistency**: All 6 modules will follow identical structure and naming
5. **Documentation Accuracy**: RULES files now reflect actual implementation

### 5.2 Negative / Trade-offs

1. **Setup Overhead**: Requires PYTHONPATH configuration for import script (mitigated by using pytest in CI)
2. **Test Environment**: Integration tests still need database (PostgreSQL/SQLite test instance)

### 5.3 Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Import paths still wrong | Validation script catches before merge |
| Naming inconsistency | Explicit conventions in HEXAGONAL_RULES.yaml |
| Other modules miss pattern | Same checklist applied to all 6 modules |
| Script breaks future | Maintains as living document, versioned with ADRs |

---

## 6. Validation Approach for Remaining Modules

### For Phases 2-6 (Bookshelf, Book, Block, Tag, Media)

Apply same P0/P1/P2 strategy:

```bash
# P0: Check critical files
grep "from infra.database import Base" backend/infra/database/models/{module}_models.py
grep "class SQLAlchemy{Entity}Repository(I{Entity}Repository)" backend/infra/storage/{module}_repository_impl.py

# P1: Update RULES files
# - DDD_RULES.yaml: {module}.implementation_files → infra paths
# - HEXAGONAL_RULES.yaml: verify port/adapter mappings

# P2: Run verification script
python tools/verify_library.py  # (copy script to tools/verify_{module}.py for each module)
pytest backend/api/app/tests/test_{module}/ -q
```

---

## 7. Configuration & Reference

### 7.1 Import Path Standards (All Modules)

```python
# Domain layer (pure logic, no imports from infra/)
from modules.{module}.domain.{entity} import {Entity}

# Application layer (UseCase ports)
from modules.{module}.application.ports.input import I{Entity}UseCase
from modules.{module}.application.ports.output import I{Entity}Repository

# Infrastructure layer (adapters)
from infra.storage.{module}_repository_impl import SQLAlchemy{Entity}Repository
from infra.database.models.{module}_models import {Entity}Model

# HTTP layer (router, only in routers/ file)
from modules.{module}.routers.{module}_router import router
```

### 7.2 File Structure Template (For Each Module)

```
api/app/modules/{module}/
├── domain/
│   ├── {entity}.py                 (AggregateRoot, pure logic)
│   ├── {entity_name}.py            (ValueObject)
│   └── events.py                   (DomainEvents)
├── application/
│   ├── ports/
│   │   ├── input.py                (I{Entity}UseCase interfaces + DTOs)
│   │   └── output.py               (I{Entity}Repository interface)
│   └── use_cases/
│       ├── create_{entity}.py      (CreateUseCase)
│       ├── get_{entity}.py         (GetUseCase)
│       └── delete_{entity}.py      (DeleteUseCase)
├── routers/
│   └── {module}_router.py          (FastAPI endpoints with UseCase DI)
├── exceptions.py                   (Domain exceptions)
├── schemas.py                      (Pydantic DTOs)
└── __init__.py                     (Public exports)

backend/infra/
├── storage/
│   └── {module}_repository_impl.py (SQLAlchemy{Entity}Repository)
└── database/
    └── models/
        └── {module}_models.py      (ORM models with infra.database.Base)
```

### 7.3 Naming Convention Reference Card

| Component | Pattern | Example |
|-----------|---------|---------|
| Port Interface | `I{Entity}Repository` | `ILibraryRepository` |
| Adapter Class | `SQLAlchemy{Entity}Repository` | `SQLAlchemyLibraryRepository` |
| ORM Model Class | `{Entity}Model` | `LibraryModel` |
| ORM Model File | `{module}_models.py` (plural) | `library_models.py` |
| UseCase Class | `{Action}{Entity}UseCase` | `CreateLibraryUseCase` |
| Router File | `{module}_router.py` | `library_router.py` |
| Domain Class | `{Entity}` | `Library` |
| Value Object | `{Entity}{Property}` | `LibraryName` |

---

## 8. Integration with CI/CD

Recommended additions to CI/CD pipeline:

```yaml
# .github/workflows/validate-architecture.yml (example)
validate-architecture:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - name: Verify Library Module Architecture
      run: |
        python -m venv .venv
        source .venv/bin/activate
        pip install -r backend/requirements.txt
        python tools/verify_library.py || exit 1
    - name: Check naming conventions
      run: |
        grep -r "^class SQLAlchemy" backend/infra/storage/ | grep "Repository"
        grep -r "^class I[A-Z].*Repository" backend/api/app/modules/*/application/ports/output.py
```

---

## 9. References

- **ADR-030**: Port-Adapter Separation Pattern (I-prefix convention established)
- **ADR-012**: ORM Model Strategy (models in infra/database/models/)
- **HEXAGONAL_RULES.yaml**: Architecture patterns and port/adapter mappings
- **DDD_RULES.yaml**: Domain rules and invariants (now with updated file paths)
- **tools/verify_library.py**: Executable validation script

---

## 10. Rollout Timeline

| Phase | Module | Validation | Target |
|-------|--------|-----------|--------|
| 1 | Library | ✅ P0/P1 | ✅ COMPLETE (Nov 14) |
| 2 | Bookshelf | ⏳ P0/P1 | Nov 15 |
| 3 | Book | ⏳ P0/P1 | Nov 15 |
| 4 | Block | ⏳ P0/P1 | Nov 16 |
| 5 | Tag | ⏳ P0/P1 | Nov 16 |
| 6 | Media | ⏳ P0/P1 | Nov 17 |
| Final | All | ✅ P2 (tests) | Nov 17-18 |

---

## 11. Decision Drivers

1. **Scalability**: Validating Library → 6 modules requires systematic approach
2. **Quality**: Architecture compliance must be verifiable, not manual
3. **Documentation**: RULES files are source of truth, must stay in sync
4. **Automation**: Scripts enable faster turnaround for remaining modules

---

**Status**: DECIDED & IMPLEMENTED
**Review Date**: November 14, 2025
**Next Review**: After Phase 2 (Bookshelf module completion)

---

*This ADR formalizes the validation approach for Library Module migration and provides blueprint for remaining 5 modules.*
