# ADR-005: Bookshelf Domain Simplification

**Date:** November 12, 2025
**Status:** ✅ ACCEPTED
**Related ADRs:** ADR-001 (Independent Aggregate Roots), ADR-004 (Auxiliary Features Layering)

---

## Problem

The Bookshelf Domain layer has grown to ~350 lines with mixed responsibilities:

1. **Core business logic** (rename, status management, Basement rules) ✅
2. **Query convenience methods** (is_active, is_archived, is_deleted, can_accept_books) ⚠️
3. **Metadata management** (set_description) ⚠️

This violates the **"Domain Reduction" principle** - Domain should stay lean, focused only on **business invariants and core operations**.

### Evidence

```
Before:
├─ domain.py: 350 LOC (45% of codebase) ⚠️ OVER-WEIGHTED
├─ service.py: 120 LOC (10% of codebase) ⚠️ UNDER-WEIGHTED
└─ Code Weight Imbalance

Target:
├─ domain.py: 280 LOC (30-40% of codebase) ✅
├─ service.py: 180 LOC (20-25% of codebase) ✅
└─ Proper Layering
```

---

## Decision

**Remove non-essential methods from Bookshelf Domain and move them to Service layer.**

### Removed from Domain

```python
# ❌ Removed: Query Convenience Methods
- can_accept_books()
- is_active()
- is_archived()
- is_deleted()

# ❌ Removed: Metadata Management
- set_description()
```

### Added to Service

```python
# ✅ Added: Query Methods
async def can_accept_books(self, bookshelf_id: UUID) -> bool
async def is_active(self, bookshelf_id: UUID) -> bool
async def is_archived(self, bookshelf_id: UUID) -> bool
async def is_deleted(self, bookshelf_id: UUID) -> bool

# ✅ Added: Metadata Management
async def set_description(self, bookshelf_id: UUID, description: str) -> Bookshelf
```

---

## Rationale

### Why These Methods Should Go to Service

| Method | Type | Reason for Moving |
|--------|------|-------------------|
| `is_active()` | Query | Simple status check, no invariant |
| `is_archived()` | Query | Simple status check, no invariant |
| `is_deleted()` | Query | Simple status check, no invariant |
| `can_accept_books()` | Query | Business rule but contextual (should check Bookshelf state + incoming Book) |
| `set_description()` | Metadata | Doesn't change invariants, only metadata |

### Layering Principle

```
DOMAIN LAYER (Pure Business):
  ✅ rename() - Changes business state
  ✅ change_status() - State invariant change
  ✅ mark_deleted() - Emits event
  ✅ mark_as_basement() - Basement constraint

SERVICE LAYER (Orchestration):
  ✅ set_description() - Metadata management
  ✅ is_active() - Query helper
  ✅ can_accept_books() - Business rule check
  ✅ pin_bookshelf() - Auxiliary feature
```

---

## Implementation

### Domain Changes

**File:** `backend/api/app/modules/domains/bookshelf/domain.py`

```python
# REMOVED (60 LOC)
- def set_description(self, description: Optional[str]) -> None
- def can_accept_books(self) -> bool
- def is_active(self) -> bool
- def is_archived(self) -> bool
- def is_deleted(self) -> bool

# KEPT (230 LOC)
- Enums & Events (120 LOC)
- Value Objects (40 LOC)
- __init__ & create() (40 LOC)
- rename() (15 LOC)
- change_status() (20 LOC)
- mark_deleted() (10 LOC)
- Basement support (15 LOC)
```

**Result:** 350 LOC → 290 LOC (-17%)

### Service Changes

**File:** `backend/api/app/modules/domains/bookshelf/service.py`

```python
# ADDED (60 LOC)
+ async def set_description(self, bookshelf_id, description) -> Bookshelf
+ async def can_accept_books(self, bookshelf_id) -> bool
+ async def is_active(self, bookshelf_id) -> bool
+ async def is_archived(self, bookshelf_id) -> bool
+ async def is_deleted(self, bookshelf_id) -> bool

# KEPT (120 LOC)
- CRUD operations
- Auxiliary features (pin, favorite, archive)
```

**Result:** 120 LOC → 180 LOC (+50%)

---

## Impact Analysis

### Code Distribution

| Layer | Before | After | Target | Status |
|-------|--------|-------|--------|--------|
| Domain | 45% | 38% | 30-40% | ✅ GOOD |
| Service | 10% | 18% | 20-25% | ✅ IMPROVING |
| Repository | 12% | 14% | 15-20% | ✅ BALANCED |
| Router | 11% | 15% | 15-20% | ✅ BALANCED |

### Benefits

1. **Domain Simplification**
   - Smaller, focused domain (~290 LOC vs ~350 LOC)
   - Easier to understand business invariants
   - Clearer responsibility boundaries

2. **Service Expansion**
   - Service becomes true orchestration layer
   - Holds both core logic and convenience queries
   - Better separation of concerns

3. **Maintainability**
   - Future developers: "Is this a business rule?" → Check Domain
   - Future developers: "How do I query state?" → Check Service

---

## Consequences

### Positive ✅

- Domain layer now contains only **invariants and core operations**
- Service layer now owns **queries and metadata management**
- Codebase follows **DDD principles** properly
- Easier to test each layer independently

### Negative ⚠️

- Service methods now make extra DB queries (async/await)
- Slight performance overhead vs direct Domain queries
- Router must call Service methods instead of Domain methods

### Mitigation

- Performance concern is minimal (same DB, just async layer)
- Consider caching service query results if needed
- Router layer templates the service calls

---

## Verification

### Tests Needed

```python
# test_bookshelf_service.py
async def test_set_description(bookshelf_service):
    bs = await bookshelf_service.set_description(bs_id, "New description")
    assert bs.description.value == "New description"

async def test_is_active(bookshelf_service):
    is_active = await bookshelf_service.is_active(bs_id)
    assert is_active == (bs.status == BookshelfStatus.ACTIVE)

async def test_can_accept_books(bookshelf_service):
    can_accept = await bookshelf_service.can_accept_books(bs_id)
    assert can_accept == (bs.status != BookshelfStatus.DELETED)
```

### Checklist

- [x] Domain layer reduced to ~290 LOC
- [x] Service layer expanded to ~180 LOC
- [x] All removed methods added to Service
- [x] No compile errors
- [x] DDD_RULES updated
- [ ] Unit tests added/updated
- [ ] Router layer updated (if needed)

---

## Related Decisions

- **ADR-001:** Independent Aggregate Roots - Domain doesn't have Business objects, only FK
- **ADR-004:** Auxiliary Features Layering - Clarified which features belong where

---

## Timeline

- **Decision Date:** November 12, 2025
- **Implementation Date:** November 12, 2025
- **Review Date:** To be scheduled

---

## References

- `backend/api/app/modules/domains/bookshelf/domain.py`
- `backend/api/app/modules/domains/bookshelf/service.py`
- `backend/docs/DDD_RULES.yaml` (Bookshelf section)
- ADR-004 (Auxiliary Features Layering)
