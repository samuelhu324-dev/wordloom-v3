# ADR-068: Complete DI Implementation and Async Repository Migration (Nov 17, 2025)

**Date**: November 17, 2025
**Status**: ACCEPTED (Hybrid Mode Implemented)
**Related ADRs**: ADR-054 (API Bootstrap), ADR-067 (DIContainer Complete Implementation)

## Problem

The backend faced a critical architectural conflict between async FastAPI routes and sync SQLAlchemy Repository implementations:

1. **Async/Sync Mismatch**:
   - Routes are async (`async def create_bookshelf()`)
   - Repositories use sync patterns (`.query()`, `.commit()` without `await`)
   - Mixing leads to TypeErrors: "object NoneType can't be used in 'await' expression"

2. **Incomplete DIContainer**:
   - Initially 22 UseCase factory methods were missing (6 Bookshelf + 8 Book + 8 Block)
   - Without DIContainer, routes couldn't instantiate UseCases

3. **Parameter Mapping Failures**:
   - UseCase.execute() signatures didn't match route request objects
   - Example: CreateBookUseCase expected (bookshelf_id, library_id, title, description) but received CreateBookRequest object
   - Response DTO conversion logic failed due to ValueObject properties (title.value, status.value)

4. **Infrastructure Urgency**:
   - Frontend integration tests blocked
   - Need working backend infrastructure by Nov 17
   - Database connection verified but Repository layer non-functional

## Decision

Implement **Hybrid Mode (Nov 17, 2025)** with selective async migration:

### Phase 1: Immediate (Nov 17 - TODAY)
1. **Library Repository**: Convert to async (SQLAlchemy async pattern)
   - Change: `Session` → `AsyncSession`
   - Change: `.query()` → `select()` with `await`
   - Change: `.commit()` → `await .commit()`

2. **22 UseCase Factory Methods**: Implement all (completed Nov 17)
   - Bookshelf: 6 methods (Create, List, Get, Delete, Restore, Rename)
   - Book: 8 methods (Create, List, Get, Update, Delete, Move, Restore, ListDeleted)
   - Block: 8 methods (Create, List, Get, Update, Reorder, Delete, Restore, ListDeleted)

3. **Bookshelf/Book/Block Repositories**: Use InMemory pattern for quick verification
   - In-memory storage for fast testing
   - No database I/O during integration tests
   - Enables full endpoint verification before async migration

4. **Response Transformation**: Fix ValueObject serialization
   - Added hasattr() checks for optional properties
   - Handle Enum.value conversion
   - Support datetime.isoformat() conversion

### Phase 2: Gradual Migration (Nov 18 onward)
- Migrate Bookshelf Repository to async (copy Library pattern)
- Migrate Book Repository to async
- Migrate Block Repository to async
- Update all 22 UseCase calls with correct parameter mapping
- Remove InMemory Repository layer

### Rationale
- **Speed**: InMemory allows frontend integration testing without persistence
- **Safety**: Library async pattern serves as template for other repositories
- **Risk Mitigation**: One repository at a time reduces blocking issues
- **Cost**: ~30 min per repository, total 2-3 hours for complete async migration

## Architecture Changes

### Before (Broken)
```
Routes (async) → DIContainer (incomplete, 0/22 methods)
              ↘ Repositories (sync: .query(), .commit())
                ❌ TypeError: can't await sync result
```

### After (Hybrid Mode)
```
Routes (async)
  ↓
DIContainer (22/22 methods ✅)
  ├→ Library UseCase → SQLAlchemyLibraryRepository (async ✅)
  │   └→ AsyncSession + select() + await
  │
  ├→ Bookshelf UseCase → InMemoryBookshelfRepository (temporary)
  │   └→ dict storage (no DB I/O)
  │
  ├→ Book UseCase → InMemoryBookRepository (temporary)
  │   └→ dict storage (no DB I/O)
  │
  └→ Block UseCase → InMemoryBlockRepository (temporary)
      └→ dict storage (no DB I/O)
```

### After Complete Migration (Target State)
```
Routes (async)
  ↓
DIContainer (22/22 methods ✅)
  ├→ Library UseCase → SQLAlchemyLibraryRepository (async ✅)
  ├→ Bookshelf UseCase → SQLAlchemyBookshelfRepository (async ✅)
  ├→ Book UseCase → SQLAlchemyBookRepository (async ✅)
  └→ Block UseCase → SQLAlchemyBlockRepository (async ✅)
     (All use AsyncSession + select() + await pattern)
```

## Implementation Details

### Library Repository Async Pattern (Template)
```python
# Before (Sync - ❌)
async def save(self, library: Library) -> None:
    model = LibraryModel(...)
    self.session.add(model)
    self.session.commit()  # ❌ Not awaited, sync call

# After (Async - ✅)
async def save(self, library: Library) -> None:
    model = LibraryModel(...)
    self.session.add(model)
    await self.session.commit()  # ✅ Awaited, async call

# Query Pattern Change
# Before: model = self.session.query(LibraryModel).filter(...).first()
# After: stmt = select(LibraryModel).where(...)
#        result = await self.session.execute(stmt)
#        model = result.scalar_one_or_none()
```

### DIContainer Factory Methods (22/22 Complete)
```python
class DIContainerInMem:
    # Bookshelf (6 methods)
    def get_create_bookshelf_use_case(self)
    def get_list_bookshelves_use_case(self)
    def get_get_bookshelf_use_case(self)
    def get_delete_bookshelf_use_case(self)
    def get_restore_bookshelf_use_case(self)
    def get_rename_bookshelf_use_case(self)

    # Book (8 methods)
    def get_create_book_use_case(self)
    def get_list_books_use_case(self)
    def get_get_book_use_case(self)
    def get_update_book_use_case(self)
    def get_delete_book_use_case(self)
    def get_move_book_use_case(self)
    def get_restore_book_use_case(self)
    def get_list_deleted_books_use_case(self)

    # Block (8 methods)
    def get_create_block_use_case(self)
    def get_list_blocks_use_case(self)
    def get_get_block_use_case(self)
    def get_update_block_use_case(self)
    def get_reorder_blocks_use_case(self)
    def get_delete_block_use_case(self)
    def get_restore_block_use_case(self)
    def get_list_deleted_blocks_use_case(self)
```

### Response DTO Transformation Fix
```python
# Before: Direct from_domain() failed on ValueObject conversion
response = BookResponse.from_domain(book)

# After: Manual dict conversion with safety checks
response_data = {
    "id": str(book.id),
    "title": str(book.title),  # BookTitle.__str__() works ✅
    "status": book.status.value if hasattr(book.status, 'value') else str(book.status),
    "created_at": book.created_at.isoformat() if hasattr(book, 'created_at') and book.created_at else None,
}
```

## Consequences

### Positive ✅
1. **Unblocked Frontend Integration**: InMemory repositories enable immediate endpoint testing
2. **Clear Migration Path**: Library pattern as template for other repositories
3. **Low Risk**: One repository at a time, ~30 min each
4. **Database Ready**: PostgreSQL connection verified, just need async layer
5. **Full DIContainer**: All 22 UseCase factory methods available

### Negative ⚠️
1. **Temporary Data Loss**: InMemory repositories don't persist (in-process only)
   - Mitigation: Acceptable for integration testing phase
   - Alternative: Use database after Library Repository verified

2. **Partial Real Implementation**: Mixed async/in-memory pattern
   - Mitigation: Clear roadmap for migration
   - Target: Complete async migration by Nov 18-19

3. **Technical Debt**: Need to complete async migration within 24 hours
   - Risk: If not completed, frontend data won't persist
   - Mitigation: Set hard deadline for Bookshelf → Book → Block migration

## Testing Strategy

### Phase 1 (Nov 17 - Today)
```
✅ Health endpoint: GET /api/v1/health → 200
✅ Library creation: POST /api/v1/libraries → 201 (with AsyncSession)
✅ Bookshelf creation: POST /api/v1/bookshelves → 201 (InMemory)
✅ Book creation: POST /api/v1/books → 201 (InMemory)
✅ Block creation: POST /api/v1/blocks → 201 (InMemory)
```

### Phase 2 (Nov 18)
```
⏳ Library CRUD: All operations use AsyncSession
⏳ Bookshelf Repository: Async migration (copy Library pattern)
⏳ Book Repository: Async migration
⏳ Block Repository: Async migration
⏳ End-to-End: All 22 endpoints with real persistence
```

## Lessons Learned

1. **Async/Sync Compatibility**: FastAPI is fully async; repositories must be async too
   - Lesson: Design repository interfaces as async from start
   - Pattern: `async def` everywhere in async framework

2. **Dependency Injection Complexity**: Factory methods need correct signatures
   - Lesson: Use type hints and document parameter requirements
   - Pattern: Keep UseCase.execute() signatures simple and consistent

3. **Hybrid Approach for Speed**: InMemory + async template enables fast progress
   - Lesson: Temporary solutions acceptable with clear migration plan
   - Pattern: Build template, then batch-apply to other repositories

4. **Value Object Serialization**: Cannot use simple `from_domain()`
   - Lesson: Need explicit conversion for ValueObject attributes
   - Pattern: Handle Enum.value, datetime.isoformat(), optional checks

## Migration Checklist (For Nov 18)

- [ ] Verify Library Repository async working (Nov 17 ✅)
- [ ] Migrate Bookshelf Repository to async
- [ ] Migrate Book Repository to async
- [ ] Migrate Block Repository to async
- [ ] Remove InMemory Repository layer
- [ ] Run full end-to-end tests
- [ ] Update dependencies.py to use real repositories
- [ ] Deploy to production

## Related Documents

- **ADR-054**: API Bootstrap and Dependency Injection
- **ADR-067**: DIContainer Complete Implementation (22 factory methods)
- **DDD_RULES.yaml**: Domain rules and aggregate design (updated Nov 17)
- **HEXAGONAL_RULES.yaml**: Architecture patterns (updated Nov 17)

## Timeline

- **Nov 17 (Today)**:
  - ✅ DIContainer 22/22 methods
  - ✅ Library Repository async
  - ✅ InMemory pattern for Bookshelf/Book/Block
  - ⏳ Response DTO conversion fixes

- **Nov 18**:
  - ⏳ Complete Bookshelf/Book/Block async migration
  - ⏳ Remove InMemory layer
  - ⏳ Full end-to-end testing

- **Nov 19+**:
  - ⏳ Production deployment
  - ⏳ Frontend integration testing
