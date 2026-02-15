# ADR-010: Book Service & Repository Design

**Status:** Accepted
**Date:** 2025-11-12
**Author:** Architecture Team
**Related ADR:** ADR-001, ADR-008, ADR-009

## Problem Statement

The Book domain requires sophisticated Service and Repository layers to handle:

1. **library_id Redundancy** (RULE-009): Must initialize from parent Bookshelf during creation
2. **Cross-Bookshelf Transfers** (RULE-011): Move Books between Bookshelves with strict permission validation
3. **Soft Delete via Basement** (RULE-012/RULE-013): Move Books to Basement instead of hard delete
4. **Basement Retrieval** (RULE-013): Query deleted Books for restoration
5. **Exception Translation**: Database constraint violations converted to Domain exceptions
6. **Comprehensive Logging**: Detailed operation tracking for debugging

## Architecture Decision

### 1. Four-Layer Service Architecture (extends ADR-008/ADR-009)

```
Layer 1: Validation
├─ Bookshelf existence check (FK validation)
├─ Library consistency verification (library_id match)
├─ Basement protection (manual move rejection)
└─ Book deletion state checks (is_deleted checks)

Layer 2: Domain Logic
├─ Call Domain Factory: Book.create()
├─ Call Domain Methods: move_to_bookshelf(), move_to_basement(), restore_from_basement()
├─ Call Domain State Changes: rename(), change_status()
└─ Extract Domain Events from aggregate

Layer 3: Persistence
├─ Repository.save() with soft-delete field mapping
├─ Handle IntegrityError → BookAlreadyExistsError translation
└─ Logging at persistence level

Layer 4: Event Publishing
├─ Collect book.events from Domain
├─ Publish to EventBus asynchronously
└─ Exception isolation (failures don't break main flow)
```

### 2. library_id Redundancy Strategy

**Why?** Bookshelf can be deleted, leaving Books orphaned without library context.

```python
# Critical: Initialize library_id from Bookshelf during create_book()
bookshelf = await self.bookshelf_repository.get_by_id(bookshelf_id)
library_id = bookshelf.library_id  # ← Extract from parent

book = Book.create(
    bookshelf_id=bookshelf_id,
    library_id=library_id,  # ← Redundant FK for permission checks
    title=title,
    summary=summary
)
```

### 3. Permission Check Strategy for Transfers

Three-layer validation for cross-Bookshelf moves:

```python
async def move_to_bookshelf(book_id, target_bookshelf_id):
    # L1: Check target exists
    target_shelf = await bookshelf_repo.get_by_id(target_bookshelf_id)
    if not target_shelf:
        raise BookshelfNotFoundError(...)

    # L1: Check same Library (library_id consistency)
    if target_shelf.library_id != book.library_id:
        raise PermissionError("Different Library")

    # L1: Check not Basement (user can't manually move to Basement)
    if target_shelf.is_basement:
        raise ValueError("Cannot move to Basement")
```

### 4. Soft Delete Query Filtering

```python
# Default filter in all queries: soft_deleted_at IS NULL
async def get_by_id(book_id):
    stmt = select(BookModel).where(
        and_(
            BookModel.id == book_id,
            BookModel.soft_deleted_at.is_(None),  # ← Auto-exclude deleted
        )
    )
    return ...

# Explicit query for Basement (deleted Books)
async def get_deleted_books(bookshelf_id):
    stmt = select(BookModel).where(
        and_(
            BookModel.bookshelf_id == bookshelf_id,
            BookModel.soft_deleted_at.is_not(None),  # ← Only deleted
        )
    )
    return ...
```

### 5. Exception Translation Pattern

```python
async def save(book):
    try:
        model = BookModel(...)
        session.add(model)
    except IntegrityError as e:
        if "bookshelf_id" in str(e).lower():
            raise BookAlreadyExistsError(...)  # ← Domain Exception
        raise
```

## Implementation Details

### Service Layer Methods

**Four-Layer Core Operations:**
- `create_book()` - Full L1-L4 with library_id initialization
- `get_book()` - Retrieval with logging
- `list_books()` - Support RULE-005 (belongs to Bookshelf)
- `rename_book()` - With event publishing
- `move_to_bookshelf()` - Full L1-L4 with three-layer permission checks
- `delete_book()` - Soft delete via move_to_basement()
- `move_to_basement()` - Explicit Basement transfer
- `restore_from_basement()` - Restore from deleted state

**Auxiliary Features (Service-layer only):**
- `set_summary()`, `set_due_date()`
- `pin_book()` / `unpin_book()`
- `publish_book()`, `archive_book()`
- `is_draft()`, `is_published()`, `is_archived()`, `is_deleted()`, `can_edit()`

**Event Publishing:**
- `_publish_events(book)` - Collect and publish all domain events

### Repository Layer Methods

**Interface Enhancements:**
```python
class BookRepository(ABC):
    async def save(book)              # Create/update with soft-delete support
    async def get_by_id(book_id)      # Single retrieval, excludes deleted
    async def get_by_bookshelf_id()   # List active Books
    async def get_deleted_books()     # Retrieve soft-deleted (Basement)
    async def delete(book_id)         # Hard delete (rarely used)
```

**Key Implementation Features:**
- `save()` maps library_id and soft_deleted_at to ORM
- `get_by_id()` filters soft_deleted_at IS NULL
- `get_by_bookshelf_id()` orders by created_at DESC
- `get_deleted_books()` retrieves only soft_deleted books
- `_to_domain()` properly maps all fields including redundant FKs

## Implementation Checklist

- [x] Service Layer: 4-layer architecture in create_book()
- [x] Service Layer: library_id initialization from Bookshelf
- [x] Service Layer: Three-layer permission checks in move_to_bookshelf()
- [x] Service Layer: Soft delete only (no hard delete in delete_book())
- [x] Service Layer: Full logging at all operations
- [x] Service Layer: Event publishing (_publish_events)
- [x] Repository Layer: get_deleted_books() for Basement retrieval
- [x] Repository Layer: Soft-delete filtering in all queries
- [x] Repository Layer: save() with library_id mapping
- [x] Repository Layer: _to_domain() with soft_deleted_at mapping
- [x] Repository Layer: Exception translation (IntegrityError)
- [x] Repository Layer: Comprehensive error logging
- [x] Domain Layer: Book aggregate intact
- [x] Models Layer: BookModel with soft_deleted_at
- [x] Tests: Unit tests for validation layers
- [x] Tests: Integration tests for persistence
- [x] DDD_RULES.yaml: Book section updated

## Rule Coverage Mapping

| Rule | Implementation File | Method(s) | Layer(s) |
|------|-------------------|-----------|---------|
| RULE-009 (Unlimited) | service.py | create_book() | L1-L4 |
| RULE-011 (Cross-transfer) | service.py | move_to_bookshelf() | L1-L4 |
| RULE-012 (Soft delete) | service.py + repo.py | delete_book() + get_by_id() | L2-L3 |
| RULE-013 (Restore) | service.py + repo.py | restore_from_basement() + get_deleted_books() | L1-L4 |

## Comparison with Industry Standards

### Repository Pattern
- ✅ Separate domain from persistence layer
- ✅ Exception translation (DB → Domain)
- ✅ Query method expansion (soft-delete support)
- ✅ DRY principle (_to_domain helper)

### Domain-Driven Design
- ✅ Aggregate root boundaries (Book independent)
- ✅ Value objects enforcing invariants (BookTitle)
- ✅ Domain events published for cross-domain communication
- ✅ Soft delete pattern for audit trails
- ✅ Redundant FKs for permission enforcement

### Service Layer Best Practices
- ✅ Four-layer separation (validation, logic, persistence, events)
- ✅ Permission checks before domain operations
- ✅ Comprehensive logging for debugging
- ✅ Exception isolation (publish failures don't break main flow)
- ✅ Transaction boundaries at Repository level

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Orphaned Books if Bookshelf deleted | High | Redundant library_id prevents orphaning; cascade events clean up Books |
| Permission check bypass if library_id not initialized | Critical | All paths through create_book() initialize from Bookshelf; tests validate |
| Accidental hard delete via delete() method | High | delete_book() explicitly calls move_to_basement(), never delete() |
| Performance N+1 on list_books() | Medium | Use SQL joins; test with query logging; add pagination |
| Race condition on concurrent updates | Low | Optimistic locking via version field (future enhancement) |

## Related Decisions

- **ADR-001**: Independent Aggregate Roots pattern (Book not nested)
- **ADR-008**: 4-Layer Service Architecture template (directly reused)
- **ADR-009**: Bookshelf implementation (parent domain pattern)
- **DDD_RULES.yaml**: RULE-009/011/012/013, POLICY-005

## Future Considerations

1. **Optimistic Locking**: Add version field to handle concurrent updates
2. **Batch Operations**: Bulk move/delete support
3. **Event Sourcing**: Store all state changes as events
4. **Caching**: Cache get_by_bookshelf_id() results
5. **Archive Optimization**: Move archived Books to cold storage
6. **Cascade Improvements**: Auto-publish cascading events when Bookshelf deleted

## Conclusion

This architecture provides a production-ready, maintainable foundation for the Book domain by:

- **Strict permission enforcement** through three-layer validation
- **Redundant FKs** ensuring Books remain accessible after Bookshelf deletion
- **Soft-delete support** preserving data for audit and recovery
- **Clear domain boundaries** between Service (orchestration) and Repository (persistence)
- **Event-driven notifications** for cross-domain communication
- **Comprehensive logging** enabling operational visibility

The design closely mirrors ADR-008/ADR-009 patterns while adding Book-specific considerations (library_id initialization, cross-transfer permissions, Basement retrieval).

---

**References:**
- ADR-001: Independent Aggregate Roots
- ADR-008: Library Service & Repository Design
- ADR-009: Bookshelf Service & Repository Design
- DDD_RULES.yaml: Book Domain section (RULE-009 through RULE-013)
- REVISION_SUMMARY_2025-11-12.md: Book module modifications
