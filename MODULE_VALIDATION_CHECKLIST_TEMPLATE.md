# Module Validation Checklist Template (P0/P1/P2)

**Template for**: Bookshelf, Book, Block, Tag, Media modules
**Based on**: Library Module successful validation (Nov 14, 2025)
**Instructions**: Copy this checklist for each module, replace `{module}` and `{Entity}` with actual names

---

## Module: {module} | Entity: {Entity}

**Start Date**: ___________
**Validator**: ___________
**Status**: ⏳ IN PROGRESS

---

## ✅ P0: File Correctness Verification

### P0.1: ORM Model File
- [ ] **File exists**: `backend/infra/database/models/{module}_models.py`
- [ ] **Import check**: Verify first line is `from infra.database import Base`
  ```bash
  grep "from infra.database import Base" backend/infra/database/models/{module}_models.py
  ```
- [ ] **Class definition**: `class {Entity}Model(Base)` exists
- [ ] **Table name**: `__tablename__ = "{module}s"` (plural)
- [ ] **Primary key**: UUID field with `primary_key=True`
- [ ] **Fields**: All required domain fields present
- [ ] **No circular imports**: No imports from `api.app.modules.*`
- [ ] **Timestamps**: `created_at`, `updated_at` with timezone awareness

**Result**: ✅ PASS / ❌ FAIL

**Notes**:
```


```

---

### P0.2: Repository Adapter File
- [ ] **File exists**: `backend/infra/storage/{module}_repository_impl.py`
- [ ] **Class exists**: `class SQLAlchemy{Entity}Repository(I{Entity}Repository)`
  ```bash
  grep "class SQLAlchemy{Entity}Repository" backend/infra/storage/{module}_repository_impl.py
  ```
- [ ] **Inherits interface**: Check `(I{Entity}Repository)` inheritance
  ```bash
  grep "class SQLAlchemy{Entity}Repository(I{Entity}Repository)" backend/infra/storage/{module}_repository_impl.py
  ```
- [ ] **Methods implemented**: `save()`, `get_by_id()`, `delete()` (at minimum)
- [ ] **Error handling**: `IntegrityError` caught and translated to domain exception
- [ ] **Async methods**: All DB methods are `async def`
- [ ] **Session management**: Proper session cleanup (flush, commit, rollback)
- [ ] **No router imports**: No imports from `api.app.modules.*.routers`

**Result**: ✅ PASS / ❌ FAIL

**Evidence** (paste command output):
```


```

---

### P0.3: Router/HTTP Adapter File
- [ ] **File exists**: `backend/api/app/modules/{module}/routers/{module}_router.py`
- [ ] **No direct repository access**: Search for `repository` or `Repository` imports
  ```bash
  grep "from infra.storage" backend/api/app/modules/{module}/routers/{module}_router.py
  ```
  (Should return NOTHING)
- [ ] **UseCase-only imports**: All imports are `from ..application.use_cases`
- [ ] **DI pattern**: UseCase injected via `Depends()`
  ```python
  async def get_{entity_snake}_usecase(...) -> {Entity}UseCase:
      repository = SQLAlchemy{Entity}Repository(session)
      return {Entity}UseCase(repository=repository)

  @router.post()
  async def create_{entity_snake}(use_case: {Entity}UseCase = Depends(get_{entity_snake}_usecase)):
  ```
- [ ] **Endpoints**: At least 4 endpoints (POST, GET, PUT/PATCH, DELETE)
- [ ] **No service imports**: No `from ..services` or deleted service.py references
- [ ] **Response schemas**: Use Pydantic models, not domain models

**Result**: ✅ PASS / ❌ FAIL

**Router endpoints found**:
```


```

---

### P0.4: Module __init__.py Cleanup
- [ ] **File path**: `backend/api/app/modules/{module}/__init__.py`
- [ ] **No deleted file references**: grep for `service.py`, old `repository.py`
  ```bash
  grep -E "service|repository" backend/api/app/modules/{module}/__init__.py
  ```
- [ ] **Imports correct**: Only imports from domain, application, routers (not infra)
- [ ] **Public exports**: Exports domain classes, exceptions, DTOs

**Result**: ✅ PASS / ❌ FAIL

**Notes**:
```


```

---

## ✅ P1: Documentation Consistency

### P1.1: DDD_RULES.yaml Update
- [ ] **File**: `backend/docs/DDD_RULES.yaml`
- [ ] **Section exists**: `{module}:` domain rule section
- [ ] **implementation_files path updated**:
  ```yaml
  implementation_files:
    - "backend/infra/database/models/{module}_models.py"  # ✅ Points to infra/
  ```
- [ ] **NOT pointing to old location**:
  ```yaml
  # ❌ OLD (WRONG):
  implementation_files:
    - "backend/api/app/modules/{module}/models.py"
  ```
- [ ] **Port/adapter documented**: IRepository → SQLAlchemyRepository referenced
- [ ] **No service.py references**: No old service layer paths

**Result**: ✅ PASS / ❌ FAIL

**Evidence** (paste relevant section):
```


```

---

### P1.2: HEXAGONAL_RULES.yaml Verification
- [ ] **File**: `backend/docs/HEXAGONAL_RULES.yaml`
- [ ] **Port mapping exists**:
  ```yaml
  - port_interface: "I{Entity}Repository"
    adapter_class: "SQLAlchemy{Entity}Repository"
  ```
- [ ] **ORM model documented**:
  ```yaml
  - module: "{module}"
    class_name: "{Entity}Model"
    base: "infra.database.Base"
    file_path: "backend/infra/database/models/{module}_models.py"
  ```
- [ ] **Naming conventions section exists** (should mention):
  - `I{Entity}Repository` for port interfaces
  - `SQLAlchemy{Entity}Repository` for adapters
  - `{module}_models.py` (plural) for ORM files

**Result**: ✅ PASS / ❌ FAIL

**Evidence** (paste relevant lines):
```


```

---

### P1.3: Pattern Consistency Check
- [ ] **Matches Library module pattern**: Port interface prefix `I`, Adapter prefix `SQLAlchemy`
- [ ] **Naming follows conventions**: No deviations (e.g., `{Entity}Repository`, `get_{entity}_repo`)
- [ ] **File structure identical**:
  ```
  api/app/modules/{module}/
  ├── domain/
  ├── application/
  ├── routers/
  ├── exceptions.py
  ├── schemas.py
  └── __init__.py

  infra/storage/
  └── {module}_repository_impl.py

  infra/database/models/
  └── {module}_models.py
  ```

**Result**: ✅ PASS / ❌ FAIL

**Deviations noted**:
```


```

---

## ✅ P2: Verification & Quality Gates

### P2.1: Static Import Verification
- [ ] **Script created**: `tools/verify_{module}.py` (optional, can reuse verify_library.py)
- [ ] **Run verification**:
  ```bash
  cd backend
  export PYTHONPATH=.:$PYTHONPATH
  python ../tools/verify_library.py
  # Or create module-specific version
  python ../tools/verify_{module}.py
  ```
- [ ] **All imports pass**: No `ModuleNotFoundError` or `ImportError`
- [ ] **Interface check passes**: `isinstance(SQLAlchemy{Entity}Repository, I{Entity}Repository)`

**Result**: ✅ PASS / ❌ FAIL

**Script output**:
```


```

---

### P2.2: Code Search Verification (Alternative to Script)
- [ ] **Port interface exists**:
  ```bash
  grep -r "class I{Entity}Repository" backend/api/app/modules/{module}/
  ```
- [ ] **Adapter implements port**:
  ```bash
  grep "class SQLAlchemy{Entity}Repository(I{Entity}Repository)" backend/infra/storage/
  ```
- [ ] **No circular dependencies**:
  ```bash
  grep -r "from infra\." backend/api/app/modules/{module}/domain/
  # Should return NOTHING
  ```

**Result**: ✅ PASS / ❌ FAIL

**Evidence**:
```


```

---

### P2.3: ADR-032 Generated (Optional)
- [ ] **File**: `assets/docs/ADR/ADR-032-{module}-structure.md` (optional, use ADR-031 as reference)
- [ ] **Sections**: Decision, rationale, implementation, consequences
- [ ] **Specific to {module}**: Documents unique constraints or requirements
- [ ] **Links to ADR-031**: References parent architecture decision

**Result**: ⏳ OPTIONAL / ✅ DONE

---

### P2.4: Test Strategy Documented
- [ ] **Test files planned**: test_domain.py, test_use_cases.py, test_repository.py, test_router.py
- [ ] **Test templates copied**: From TESTING_STRATEGY_LIBRARY_MODULE.md
- [ ] **Module-specific tests**: Updated for {Entity} and {module}
- [ ] **Test count estimated**: Domain (5-8), UseCase (4-6), Repository (4-6), Router (6-8)

**Result**: ⏳ PENDING / ✅ READY

**Test templates status**:
```


```

---

## Summary

### Validation Results

| Tier | Item | Status | Notes |
|------|------|--------|-------|
| P0 | ORM Models | ✅/❌ | |
| P0 | Repository Adapter | ✅/❌ | |
| P0 | HTTP Router | ✅/❌ | |
| P0 | Module __init__.py | ✅/❌ | |
| P1 | DDD_RULES.yaml | ✅/❌ | |
| P1 | HEXAGONAL_RULES.yaml | ✅/❌ | |
| P1 | Pattern Consistency | ✅/❌ | |
| P2 | Import Verification | ⏳/✅ | |
| P2 | Code Search Verification | ✅/❌ | |
| P2 | ADR Generated | ⏳/✅ | |
| P2 | Tests Documented | ⏳/✅ | |

---

### Issues Found

| Issue | Severity | Location | Fix |
|-------|----------|----------|-----|
| | | | |
| | | | |
| | | | |

---

### Approval

- [ ] P0 Approved by: ___________
- [ ] P1 Approved by: ___________
- [ ] P2 Approved by: ___________

**Overall Status**: ✅ APPROVED / ⏳ PENDING / ❌ BLOCKED

**Ready for next module**: YES / NO

**Sign-off Date**: ___________

---

## Next Steps

1. [ ] Implement tests using TESTING_STRATEGY_LIBRARY_MODULE.md templates
2. [ ] Run pytest: `pytest api/app/tests/test_{module}/ -v`
3. [ ] Achieve ≥80% code coverage
4. [ ] Move {module} to "tested" phase
5. [ ] Proceed to next module or merge

**Estimated time to complete**: _____ days

---

**Template Version**: 1.0
**Created**: November 14, 2025
**Based on**: Library Module validation (ADR-031)

---

**Instructions for next module**:
1. Copy this entire template
2. Replace all `{module}` with actual module name (e.g., "bookshelf")
3. Replace all `{Entity}` with actual entity name (e.g., "Bookshelf")
4. Work through each section methodically
5. Record all findings in the provided spaces
6. Save completed checklist in root or `/docs/checklists/` directory
7. Use as basis for PR review
