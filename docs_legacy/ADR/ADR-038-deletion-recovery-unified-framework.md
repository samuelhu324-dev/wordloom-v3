# ADR-038: Deletion & Recovery Unified Framework

**Status:** ✅ ACCEPTED & IN IMPLEMENTATION
**Date:** November 14, 2025
**Author:** Wordloom Architecture Team
**Stakeholders:** Product Team, QA Team, Backend Development Team
**Related ADRs:** ADR-036 (Bookshelf Testing), ADR-037 (Library Testing), DDD_RULES.yaml, HEXAGONAL_RULES.yaml
**Design Reference:** assets/docs/QuickLog/D33-WordloomDev/2. HexagnoalArchitecture/7_BasementPaperballsVault.md

---

## Executive Summary

Established a **unified deletion & recovery framework** across Wordloom to address the critical architectural gap in how different entity types handle soft deletes and recovery workflows.

**Three Core Concepts:**
- **Basement**: Global view of all soft-deleted Library/Bookshelf/Book entities (not a new container)
- **Paperballs**: Per-Book local trash for soft-deleted Blocks with position recovery support (design complete, implementation pending)
- **Vault**: User file asset lifecycle management (partially implemented via Media module)

**Phase 1 Scope:** Library + Bookshelf modules
**Status:** Design ✅ | Partial Implementation ⏳ | ADR & Rules Codification ✅

---

## Background

### Problem Statement

Previous implementation had **inconsistent deletion semantics**:

1. **Library**: No soft delete mechanism (incomplete)
   - `DeleteLibraryUseCase` existed but no ORM support (`soft_deleted_at` field missing)
   - No Basement integration

2. **Bookshelf**: Used `status` enum (ACTIVE/ARCHIVED/DELETED) without timestamp
   - Worked functionally but lacked audit trail (`soft_deleted_at` field)
   - RULE-010 (Basement protection) implemented but fragile

3. **Book**: Had `soft_deleted_at` but no "restore position" tracking
   - Could recover Book to Basement, but User Experience was basic
   - No "restore to original bookshelf" rules

4. **Block**: `soft_deleted_at` existed but missing `previous_position`
   - Paperballs concept undefined
   - No position recovery strategy

5. **Media**: Different deletion model (trash + 30-day purge)
   - Not unified with soft delete pattern
   - Vault concept partially realized

### Consequences of Previous State

- 🔴 **Critical**: Book deletion doesn't properly invoke domain method (direct repo.delete)
- 🟡 **Important**: No clear recovery rules when parent entity is deleted
- 🟡 **Important**: Block position recovery impossible (no previous_position tracking)
- 🔴 **Critical**: If this isn't fixed now, later schema migrations will be painful
- 🔴 **Critical**: Frontend API contracts don't exist (BasementShelfGroup DTO undefined)

---

## Solution Design

### 1. Unified Soft Delete Strategy

All entity deletions follow this pattern:

```
domain: Entity.mark_deleted() / move_to_basement()
  → Emits DomainEvent (e.g., BookMovedToBasement)
  ↓
application: UseCase calls domain method + publishes event
  → Event includes recovery context (original_position, original_bookshelf_id, etc.)
  ↓
infrastructure: Repository saves ORM model with soft_deleted_at ≠ null
  → Timestamp recorded for audit trail
  ↓
query: Filtering applies soft delete filter automatically
  → WHERE soft_deleted_at IS NULL (for active entities)
```

### 2. Basement – Global Deletion View

#### 2.1 Concept

- **Type**: Application Concept + View, NOT a domain entity
- **Purpose**: Unified interface for viewing and recovering soft-deleted Library/Bookshelf/Book entities
- **UI Representation**: Grouped by Bookshelf (e.g., "Books from Shelf A", "Deleted Shelves", "Orphaned Books")

#### 2.2 Data Structure

```python
# DTO Structure
class BasementViewResponse:
    library_id: UUID
    deleted_libraries_count: int
    shelf_groups: list[BasementShelfGroup]

class BasementShelfGroup:
    bookshelf_id: Optional[UUID]            # None if bookshelf was deleted/missing
    bookshelf_name: str                      # Original shelf name
    bookshelf_deleted: bool                  # True: shelf itself is deleted
    books_count: int
    books: list[BasementBookItem]

class BasementBookItem:
    book_id: UUID
    title: str
    deleted_at: datetime
    original_bookshelf_name: Optional[str]
    preview: str                             # First 200 chars of content
```

#### 2.3 Invariants

| ID | Rule | Implementation |
|----|------|-----------------|
| **BASEMENT-001** | Any child entity (Book, Bookshelf) recovery requires parent to be non-deleted | Validate in UseCase before recovery |
| **BASEMENT-002** | Basement only displays soft-delete state; does not modify original relationships (bookshelf_id, library_id) | Domain never changes parent_id during soft delete |
| **BASEMENT-003** | Cannot recover child without valid parent | Throw exception if parent is null or deleted |

#### 2.4 Recovery Rules

| Scenario | Action | Rule Enforced |
|----------|--------|----------------|
| **Parent exists** (original bookshelf not deleted) | Restore directly to original bookshelf | BASEMENT-001 ✅ |
| **Parent deleted but grandparent exists** (bookshelf deleted but library exists) | Create new recovery shelf OR user selects target shelf | BASEMENT-001 (modified) + BASEMENT-003 |
| **Root deleted** (library deleted) | Block recovery until library is restored first | BASEMENT-001 + BASEMENT-003 |
| **Cascade** (recover high-level entity) | Optional: sync-restore all soft-deleted children (configurable) | BASEMENT-001, BASEMENT-002 |

#### 2.5 Implementation Status

**Library Module:**
- ✅ `LibraryModel.soft_deleted_at` field (planned in schema changes)
- ✅ `Library.mark_deleted()` domain method (planned)
- ⏳ `RestoreLibraryUseCase` (planned Phase 2.2)
- ⏳ `ListBasementBooksUseCase` (planned Phase 2.2)

**Bookshelf Module:**
- ✅ `BookshelfModel.status = DELETED` (implemented Nov 14, 2025)
- ✅ `Bookshelf.mark_deleted()` (implemented Nov 14, 2025)
- ✅ `DeleteBookshelfUseCase` with RULE-010 validation (implemented Nov 14, 2025)
- ✅ `GetBasementUseCase` auto-creates/retrieves Basement shelf (implemented Nov 14, 2025)
- ⏳ `RestoreBookshelfUseCase` (planned Phase 2.2)
- ⏳ `GetBasementBookshelvesUseCase` (planned Phase 2.2)

---

### 3. Paperballs – Per-Book Local Trash

#### 3.1 Concept

- **Type**: Application Concept + View (not a domain entity)
- **Scope**: Within a single Book only
- **Purpose**: Provide safe harbor for accidentally deleted Blocks during writing
- **Key Feature**: Position recovery strategy to restore blocks to original or nearby location

#### 3.2 Why Position Tracking Matters

When user accidentally deletes a Block, they expect:
1. "Oh no, I deleted this by mistake" (Paperballs shows it)
2. Click "Restore" → Block returns to exact or nearby position
3. NOT: Block disappears somewhere else in the document

#### 3.3 Recovery Strategies

When restoring Block from Paperballs, apply this priority:

```
Strategy 1: EXACT_RESTORE
  └─ Original position_index available AND unoccupied
  └─ Message: "已恢复到原位置（第X段）"

Strategy 2: NEARBY_RESTORE
  └─ Original position occupied by another Block
  └─ Use gap sort algorithm (Decimal gap insertion)
  └─ Message: "原位置已被占用，恢复到第X段"

Strategy 3: CHAPTER_END
  └─ Cannot find nearby position
  └─ Insert at end of original chapter
  └─ Message: "恢复到章节末尾（第X段）"

Strategy 4: BOOK_END
  └─ Original chapter deleted or no metadata
  └─ Insert at end of entire book
  └─ Message: "恢复到书末尾（第X段）"
```

#### 3.4 Required Data Model Changes

**BlockModel** needs new field:

```python
class BlockModel(Base):
    # ... existing fields ...
    soft_deleted_at: DateTime  # Already exists ✅

    # NEW: Save position before deletion
    previous_position: Numeric(precision=19, scale=10)  # Gap sort value
    # Populated when block.mark_deleted() is called
```

#### 3.5 Implementation Status

- 🔜 **Phase 2.5** (after Book and Media)
- ✅ Design complete
- 📋 ListPaperballsUseCase (planned)
- 📋 RestoreBlockFromPaperballsUseCase (planned)

---

### 4. Vault – Asset Lifecycle Management

#### 4.1 Concept

- **Type**: Aggregate (managed by Vault, not bound to Basement/Paperballs)
- **Purpose**: Manage user-uploaded file lifecycle (upload → active → trash → purge)
- **Key Difference from Basement/Paperballs**: Manages file **ownership**, not references

#### 4.2 Lifecycle

```
Upload → ACTIVE
  ↓
User deletes asset OR removes from Block → TRASH (trash_at = now)
  ↓
7-30 days → PURGED (hard delete, deleted_at = now)
```

#### 4.3 Invariants

| ID | Rule | Current Status |
|----|------|-----------------|
| **VAULT-001** | Deleting Block attachment only removes reference; Asset stays in Vault | Not yet tested |
| **VAULT-002** | True deletion happens at Vault level, not Block level | ⏳ 30-day purge task pending |

#### 4.4 Implementation Status

**Media Module:**
- ✅ `MediaModel.state` (ACTIVE/TRASH) implemented
- ✅ `MediaModel.trash_at` timestamp implemented
- ✅ `MediaModel.deleted_at` timestamp (for 30-day purge) implemented
- ✅ `MoveMediaToTrashUseCase` implemented
- ✅ `RestoreMediaUseCase` implemented
- ⏳ 30-day auto-purge scheduled task (planned Phase 2.6)

---

## Implementation Roadmap

### Phase 2.1 – Complete ✅
- ADR-036: Bookshelf Testing
- ADR-037: Library Testing
- 16/16 tests passing for Bookshelf
- 13/13 tests passing for Library

### Phase 2.2 – Library/Bookshelf Recovery Features (Next)

**Planned Deliverables:**
1. `LibraryModel.soft_deleted_at` field + migration
2. `Library.mark_deleted()`, `Library.restore()` domain methods
3. `RestoreLibraryUseCase` + tests (12 tests expected)
4. `ListBasementBooksUseCase` + tests (16 tests expected)
5. `RestoreBookshelfUseCase` + tests (8 tests expected)
6. `GetBasementBookshelvesUseCase` + tests (8 tests expected)

**Success Criteria:**
- 40+ new tests pass (100% pass rate)
- All BASEMENT-001/002/003 invariants enforced
- UI can render BasementViewResponse correctly

### Phase 2.3 – Book Module Recovery (Dependent on 2.2)

**Planned Deliverables:**
1. Enhance `Book.move_to_basement()` to track `original_bookshelf_id`
2. `RestoreBookFromBasementUseCase` with fallback strategy (auto-create vs manual-select)
3. Tests for all recovery scenarios

### Phase 2.4 – Block Module & Paperballs (Dependent on 2.3)

**Planned Deliverables:**
1. `BlockModel.previous_position` field + migration
2. `RestoreBlockFromPaperballsUseCase` with position strategy selection
3. Paperballs position recovery algorithm
4. Tests for all 4 recovery strategies

### Phase 2.5 – Media Vault Complete (Dependent on 2.4)

**Planned Deliverables:**
1. 30-day auto-purge scheduled task
2. `ListVaultAssetsUseCase`
3. Purge verification tests

---

## Rules Codification

All invariants and recovery rules have been formally added to:

### DDD_RULES.yaml
- New section: `deletion_recovery_framework`
- BASEMENT-001, BASEMENT-002, BASEMENT-003 (invariants)
- PAPERBALLS-001, PAPERBALLS-002, PAPERBALLS-003 (invariants)
- VAULT-001, VAULT-002 (invariants)
- Recovery rules for each scenario
- Implementation status per module

### HEXAGONAL_RULES.yaml
- New section: `deletion_recovery_ports`
- Port interface definitions for all new UseCases
- DTO structure specifications
- Architecture principles for deletion/recovery

---

## Risk Mitigation

### Risk 1: Data Migration Complexity
**If we wait until Phase 2.4 to add `previous_position` field:**
- Problem: Existing Blocks have no previous_position history
- Impact: Can't recovery restore deleted blocks accurately

**Mitigation:**
- ✅ Add field + migration at start of Phase 2.4
- Migration script: Set `previous_position = position_index` for all existing blocks

### Risk 2: API Contract Breakage
**If we don't define BasementViewResponse DTO early:**
- Problem: Frontend and backend disagree on shape
- Impact: Rework required mid-implementation

**Mitigation:**
- ✅ DTO fully specified in ADR and HEXAGONAL_RULES.yaml
- Frontend can build UI components now (no blocker)

### Risk 3: Test Coverage Gaps
**If we don't test recovery edge cases now:**
- Problem: Discover bugs in production when user has 10,000 deleted blocks
- Impact: Data inconsistency possible

**Mitigation:**
- Test all recovery scenarios (parent exists, parent deleted, root deleted, cascade)
- Use MockRepository for fast iteration
- 100% test pass rate required before production

---

## Decision Rationale

### Why Unified Soft Delete Pattern?

1. **Consistency**: All domains use same mechanism (soft_deleted_at + timestamp)
2. **Auditability**: Timestamps enable "who deleted what when" queries
3. **Recovery**: Soft delete allows recovery without data reconstruction
4. **Performance**: Query filtering (WHERE soft_deleted_at IS NULL) is cheap

### Why Three Separate Concepts (Basement/Paperballs/Vault)?

1. **Basement** (global): Needed for cross-library recovery workflows
2. **Paperballs** (per-book): Needed for localized "undo" during writing
3. **Vault** (asset): Completely different lifecycle (30-day purge, not user-driven recovery)

Mixing them would create confusion in code and UI.

### Why Not a Trash Container Entity?

**Rejected**: Creating a `Trash` or `RecycleBin` Bookshelf
- Problem: Would require moving Books to a special Bookshelf
- Impact: Complicates aggregates (Book has both `bookshelf_id` and `trash_bookshelf_id`?)
- Solution: Use view + soft delete instead (this ADR's approach)

---

## Acceptance Criteria

- ✅ ADR and design documents complete and linked in rules files
- ⏳ Phase 2.2 implementation complete (RestoreLibraryUseCase, etc.)
- ⏳ 40+ tests pass for all deletion/recovery scenarios
- ⏳ BASEMENT-001/002/003 invariants enforced in code
- ⏳ UI can render BasementViewResponse and PaperballsViewResponse
- ⏳ Documentation updated (README, API docs)

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| `7_BasementPaperballsVault.md` | Original design concept (in Chinese) |
| `DDD_RULES.yaml` v3.1 | Deletion framework rules formalized |
| `HEXAGONAL_RULES.yaml` v1.2 | Deletion/recovery ports defined |
| `ADR-036` | Bookshelf testing baseline |
| `ADR-037` | Library testing baseline |

---

## Implementation Checklist

### Phase 2.2 Deliverables
- [ ] `LibraryModel.soft_deleted_at` field + Alembic migration
- [ ] `Library.mark_deleted()` + `Library.restore()` domain methods
- [ ] `RestoreLibraryUseCase` implementation + 12 tests
- [ ] `ListBasementBooksUseCase` implementation + 16 tests
- [ ] `RestoreBookshelfUseCase` implementation + 8 tests
- [ ] `GetBasementBookshelvesUseCase` implementation + 8 tests
- [ ] All tests pass (100% pass rate)
- [ ] Update DDD_RULES.yaml metadata (implementation status)
- [ ] Update HEXAGONAL_RULES.yaml metadata (ports implemented count)

### Future Phases
- [ ] Phase 2.3: Book recovery enhancements
- [ ] Phase 2.4: Block Paperballs + previous_position field
- [ ] Phase 2.5: Media Vault auto-purge

---

## Appendix: DTO Examples

### Library Restoration

```python
# Request
class RestoreLibraryRequest:
    library_id: UUID

# Response
class RestoreLibraryResponse:
    library_id: UUID
    restored_at: datetime
    message: str  # "Library restored successfully"

# Event
@dataclass
class LibraryRestored(DomainEvent):
    aggregate_id: UUID  # library_id
    restored_at: datetime
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
```

### Bookshelf Restoration with Dependency Check

```python
# Request
class RestoreBookshelfRequest:
    bookshelf_id: UUID

# Response (with status info)
class RestoreBookshelfResponse:
    bookshelf_id: UUID
    library_id: UUID
    status: str  # "active"
    restored_at: datetime

# Error Cases
class ParentLibraryDeletedException(Exception):
    """Library already deleted, cannot restore Bookshelf"""
    detail: str  # BASEMENT-003 violation
```

### Basement View (Grouped Books)

```python
class BasementViewResponse:
    library_id: UUID
    total_deleted_books: int
    total_deleted_bookshelves: int
    shelf_groups: list[BasementShelfGroup]

class BasementShelfGroup:
    # Bookshelf Information
    bookshelf_id: Optional[UUID]
    bookshelf_name: str
    bookshelf_deleted: bool

    # Books Count
    books_count: int

    # Deleted Books
    books: list[BasementBookItem]

class BasementBookItem:
    book_id: UUID
    title: str
    deleted_at: datetime
    original_bookshelf_name: Optional[str]
    preview: str
    recovery_status: str  # "ready" | "waiting_parent_restore"
```

---

**Document Version:** 1.0
**Last Updated:** November 14, 2025
**Status:** ACCEPTED ✅
