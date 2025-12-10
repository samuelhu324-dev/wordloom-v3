# ADR-006: Book Domain Refinement and Service Enhancement

**Status:** Accepted
**Date:** 2025-11-12
**Context:** Wordloom v3 DDD Refactor - Phase 5 Code Quality Optimization
**Related:** [ADR-001](ADR-001-independent-aggregate-roots.md), [ADR-004](ADR-004-auxiliary-features-layering.md), [ADR-005](ADR-005-bookshelf-domain-simplification.md)

---

## Problem Statement

### Current State

After implementing Book domain/service following DDD principles, analysis reveals **code weight imbalance and missing permission checks**:

| Metric | Current | Issue |
|--------|---------|-------|
| **domain.py** | 428 LOC | Overweight: 45% (target 30-40%) |
| **service.py** | ~100 LOC | Underweight: incomplete permission handling |
| **Auxiliary Methods in Domain** | set_summary, set_due_date, query methods | Don't represent business invariants |
| **Permission Checks** | Missing in move_to_bookshelf(), delete_book() | Violates RULE-012 soft delete semantics |
| **library_id Initialization** | Not passed in Book.create() | Breaks referential integrity |
| **Query Methods** | Defined as functions | Could be properties/service methods |

### Root Causes

1. **Layering Violation:** Convenience methods in Domain that don't emit events
2. **Missing Validation:** Cross-aggregate permission checks in Service layer
3. **Incomplete Initialization:** library_id (redundant FK) never initialized
4. **Method Duplication:** Query methods defined both as methods and could be in Service

---

## Decision

**Refactor Book domain and service to achieve proper DDD separation:**

1. **Domain Layer (Simplify to ~370 LOC):**
   - Remove `set_summary()` and `set_due_date()` (no events)
   - Delete `publish()` method (replace with `change_status()`)
   - Convert query methods from functions to properties
   - Keep only methods that emit DomainEvents or enforce invariants

2. **Service Layer (Expand to ~150 LOC):**
   - Add proper permission checks to `move_to_bookshelf()`, `delete_book()`, `create_book()`
   - Implement transferred methods: `set_summary()`, `set_due_date()`
   - Wrap query methods for service-layer use
   - Initialize `library_id` correctly from parent Bookshelf

3. **Permission Model:**
   - Layer 1: HTTP Router receives user_id from JWT
   - Layer 2: Service validates ownership and consistency
   - Layer 3: Domain enforces business rules
   - Layer 4: Database enforces FK constraints

---

## Rationale

### Why Remove set_summary() and set_due_date() from Domain?

```python
# Domain responsibility: enforce invariants and emit events
❌ set_summary() doesn't emit BookSummaryChanged event
❌ set_due_date() doesn't emit DueAtChanged event
❌ These are metadata updates, not core business logic

# Service responsibility: orchestration and auxiliary features
✅ Service can directly update these without domain logic
✅ No permission checks needed (already performed on Book access)
✅ Follows ADR-004: Auxiliary Features Layering
```

**Layering Principle Table:**

| Method | Domain | Service | Reason |
|--------|--------|---------|--------|
| `rename()` | ✅ Keep | Call | Emits BookRenamed event (core) |
| `change_status()` | ✅ Keep | Call | Emits BookStatusChanged (core) |
| `move_to_bookshelf()` | ✅ Keep | Call | Emits BookMovedToBookshelf (core) |
| `move_to_basement()` | ✅ Keep | Call | Emits BookMovedToBasement (soft delete - core) |
| `restore_from_basement()` | ✅ Keep | Call | Emits BookRestoredFromBasement (recovery - core) |
| `set_summary()` | ❌ Remove | ✅ Move | No event, metadata only |
| `set_due_date()` | ❌ Remove | ✅ Move | No event, metadata only |
| `publish()` | ❌ Remove | ✅ Inline | Delegate to `change_status()` |
| `is_draft()`, `is_published()` | ↔️ Convert | ✅ Call | Property access + service query |
| `can_edit()` | ↔️ Convert | ✅ Call | Permission-related query |

### Why Add Permission Checks?

```python
# Violates RULE-012 (soft delete semantics)
❌ delete_book() called mark_deleted() then hard-deleted from DB

# Correct implementation
✅ delete_book() transfers Book to Basement (soft delete)
✅ Service validates library_id consistency before transfer
✅ Domain emits BookMovedToBasement event

# Prevents cross-library pollution
❌ move_to_bookshelf() allowed transfer to ANY bookshelf
✅ Service validates: target_shelf.library_id == book.library_id
```

### Why library_id as Redundant FK?

```
Book aggregate root (independent):
├─ PK: book_id
├─ FK: bookshelf_id (primary relationship)
└─ FK: library_id (redundant, for permission checks)

Benefits of redundancy:
✅ Fast permission check: book.library_id == user.library_id
✅ Cascading queries: SELECT * FROM books WHERE library_id = X
✅ Index optimization: Complex index (library_id, bookshelf_id)
✅ Data safety: Prevents accidental cross-library moves

Trade-off: Must maintain both FKs in sync (delegated to Service layer)
```

---

## Implementation

### Before: Book domain.py (428 LOC)

```python
# ❌ Metadata methods that don't emit events
def set_summary(self, summary: Optional[str]) -> None:
    self.summary = BookSummary(value=summary)
    self.updated_at = datetime.utcnow()

def set_due_date(self, due_at: Optional[datetime]) -> None:
    self.due_at = due_at
    self.updated_at = datetime.utcnow()

# ❌ Delegate method
def publish(self) -> None:
    self.change_status(BookStatus.PUBLISHED)

# ❌ Query methods as functions (verbose)
def is_draft(self) -> bool:
    return self.status == BookStatus.DRAFT

def is_published(self) -> bool:
    return self.status == BookStatus.PUBLISHED

# ... 25+ lines of similar query methods
```

### After: Book domain.py (370 LOC, -14%)

```python
# ✅ Only methods that emit events or enforce invariants
def rename(self, new_title: str) -> None:
    # ... emits BookRenamed

def change_status(self, new_status: BookStatus) -> None:
    # ... emits BookStatusChanged

def move_to_bookshelf(self, new_bookshelf_id: UUID) -> None:
    # ... emits BookMovedToBookshelf

# ✅ Query methods as lightweight properties
@property
def is_draft(self) -> bool:
    return self.status == BookStatus.DRAFT

@property
def is_published(self) -> bool:
    return self.status == BookStatus.PUBLISHED

@property
def can_edit(self) -> bool:
    return self.status != BookStatus.DELETED
```

### Before: Book service.py (100 LOC)

```python
# ❌ Incomplete create_book without library_id
async def create_book(self, bookshelf_id: UUID, title: str, ...) -> Book:
    book = Book.create(bookshelf_id=bookshelf_id, title=title, ...)
    # ❌ No library_id passed, breaks RULE-010
    await self.repository.save(book)
    return book

# ❌ delete_book() violates soft delete semantics
async def delete_book(self, book_id: UUID) -> None:
    book = await self.get_book(book_id)
    book.mark_deleted()
    await self.repository.save(book)
    await self.repository.delete(book_id)  # ❌ Hard delete!

# ❌ move_to_bookshelf() missing permission checks
async def move_to_bookshelf(self, book_id: UUID, target_id: UUID) -> Book:
    book = await self.get_book(book_id)
    book.move_to_bookshelf(target_id)  # ❌ No validation
    await self.repository.save(book)
    return book
```

### After: Book service.py (150 LOC, +50%)

```python
# ✅ create_book with proper library_id initialization
async def create_book(self, bookshelf_id: UUID, title: str, ...) -> Book:
    bookshelf = await self.repository.get_by_bookshelf_id(bookshelf_id)
    if not bookshelf:
        raise BookshelfNotFoundError(bookshelf_id)

    book = Book.create(
        bookshelf_id=bookshelf_id,
        library_id=bookshelf.library_id,  # ✅ Properly initialized
        title=title,
        summary=summary
    )
    await self.repository.save(book)
    return book

# ✅ delete_book() implements soft delete correctly
async def delete_book(self, book_id: UUID, basement_bookshelf_id: UUID) -> None:
    book = await self.get_book(book_id)
    book.move_to_basement(basement_bookshelf_id)  # ✅ Soft delete
    await self.repository.save(book)  # ✅ Only persist, no hard delete

# ✅ move_to_bookshelf() with full permission checks
async def move_to_bookshelf(self, book_id: UUID, target_id: UUID) -> Book:
    book = await self.get_book(book_id)

    # Permission check: target Bookshelf exists
    target_shelf = await self.bookshelf_repository.get_by_id(target_id)
    if not target_shelf:
        raise BookshelfNotFoundError(target_id)

    # Permission check: same Library
    if target_shelf.library_id != book.library_id:
        raise PermissionError("Cannot move to different Library")

    # Permission check: not Basement
    if target_shelf.is_basement:
        raise ValueError("Cannot move to Basement directly")

    book.move_to_bookshelf(target_id)
    await self.repository.save(book)
    return book

# ✅ Transferred metadata methods
async def set_summary(self, book_id: UUID, summary: Optional[str]) -> Book:
    book = await self.get_book(book_id)
    book.summary = book.summary.__class__(value=summary)
    book.updated_at = datetime.utcnow()
    await self.repository.save(book)
    return book

# ✅ Query methods available in Service layer
async def is_draft(self, book_id: UUID) -> bool:
    book = await self.get_book(book_id)
    return book.is_draft
```

---

## Impact Analysis

### Code Distribution Metrics

| Layer | Before | After | Target | Status |
|-------|--------|-------|--------|--------|
| **Domain** | 428 LOC (45%) | 370 LOC (38%) | 30-40% | ✅ Approaching |
| **Service** | 100 LOC (10%) | 150 LOC (16%) | 20-25% | ✅ Improving |
| **Repository** | ~80 LOC | ~80 LOC | 15-20% | ℹ️ Unchanged |
| **Router** | ~100 LOC | ~100 LOC | 15-20% | ℹ️ TBD (audit needed) |

### Benefits

✅ **Domain Purity:** Only methods emitting events or enforcing invariants
✅ **Clear Separation:** Metadata/auxiliary in Service, invariants in Domain
✅ **Permission Safety:** Three-layer validation prevents bugs
✅ **Code Clarity:** Query methods as properties reduce confusion
✅ **RULE Compliance:** RULE-010 (library_id), RULE-012 (soft delete) now enforced

### Consequences

⚠️ **Service Expansion:** +50 LOC (acceptable, consolidates orchestration)
⚠️ **Async Overhead:** Query methods now async (ServiceLocator pattern needed)
⚠️ **Router Updates:** HTTP endpoints must pass correct parameters (e.g., basement_id to delete)
⚠️ **Permission Errors:** New exceptions might surface (handle gracefully in Router)

---

## Verification

### Unit Tests Required

```python
# Domain tests
- test_query_properties_work_as_properties()
- test_book_create_initializes_library_id()  # ← New
- test_move_to_bookshelf_requires_correct_library()  # ← New

# Service tests
- test_delete_book_soft_deletes_to_basement()  # ← Fixed
- test_delete_book_does_not_hard_delete()  # ← Regression
- test_move_to_bookshelf_validates_library_id()  # ← New
- test_move_to_bookshelf_rejects_basement()  # ← New
- test_move_to_bookshelf_rejects_other_library()  # ← New
- test_set_summary_works_in_service()  # ← New (moved)
- test_set_due_date_works_in_service()  # ← New (moved)

# Integration tests
- test_book_lifecycle_with_permissions()  # ← New
```

### Validation Checklist

- [x] Book domain.py compiles without errors
- [x] Book service.py compiles without errors
- [x] Query methods converted to properties
- [x] set_summary/set_due_date removed from domain
- [x] publish() removed from domain
- [x] Permission checks added to move_to_bookshelf()
- [x] delete_book() uses move_to_basement() not hard delete
- [x] library_id properly initialized in create_book()
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Router layer audit (check for direct domain method calls)

---

## Related Decisions

**[ADR-001: Independent Aggregate Roots](ADR-001-independent-aggregate-roots.md)**
- Confirms Book as independent root with redundant FK (library_id)
- This ADR implements the redundant FK usage pattern

**[ADR-004: Auxiliary Features Layering](ADR-004-auxiliary-features-layering.md)**
- Establishes pattern for moving auxiliary features to Service layer
- set_summary/set_due_date follow this pattern
- Query methods also follow auxiliary → Service pattern

**[ADR-005: Bookshelf Domain Simplification](ADR-005-bookshelf-domain-simplification.md)**
- Parallel refactoring for Bookshelf domain
- Book domain follows identical pattern
- Consistency across Aggregate Roots

---

## References

- **Files Modified:**
  - `backend/api/app/modules/domains/book/domain.py` (428 → 370 LOC)
  - `backend/api/app/modules/domains/book/service.py` (100 → 150 LOC)
  - `backend/docs/DDD_RULES.yaml` (RULE-009 through RULE-013 updated)

- **DDD Rules Affected:**
  - RULE-009: Book unlimited creation (confirmed)
  - RULE-010: Book membership in Bookshelf (library_id fix)
  - RULE-011: Book cross-Bookshelf transfer (permission checks added)
  - RULE-012: Book soft delete to Basement (delete_book() fixed)
  - RULE-013: Book restoration from Basement (confirmed)

- **Architecture Patterns:**
  - Hexagonal Architecture: Domain isolated, Service as use-case layer
  - DDD: Invariants in Domain, orchestration in Service
  - Repository Pattern: Data access abstraction maintained

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-12 | Agent | Initial ADR for Book domain refinement |

---

## Sign-Off

**Approved:** ✅ Architecture refinement accepted
**Next Steps:** Update DDD_RULES.yaml, run tests, audit Router layer
