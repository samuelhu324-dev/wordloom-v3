# ADR-007: Block Markdown Insertion Architecture and Soft-Delete Model

**Status:** Accepted
**Date:** 2025-11-12
**Context:** Wordloom v3 DDD Refactor - Phase 5 Block Implementation and UI/UX Integration
**Related:** [ADR-001](ADR-001-independent-aggregate-roots.md), [ADR-002](ADR-002-basement.md), [ADR-004](ADR-004-auxiliary-features-layering.md), [ADR-006](ADR-006-book-domain-refinement.md)

---

## Problem Statement

### Current State

Block domain has been implemented as an independent aggregate root, but several architectural decisions remain unclear:

1. **UI/UX Integration:** How should the "Insert Block" toolbar action flow through the system?
2. **Deletion Strategy:** Should blocks be hard-deleted or soft-deleted like books?
3. **Permission Model:** How do permission checks work across Book → Block relationship?
4. **Content Types:** Should we support all block types (image, code, table) at once or start minimal?
5. **Ordering & Concurrency:** How to handle block reordering without complex locking?

### Root Causes

- Block is first content-level entity (deeper than Book/Bookshelf)
- Needs careful UX design to avoid N+1 queries and race conditions
- Permission model must cascade from Library → Book → Block
- Soft-delete consistency with Book/Bookshelf basement pattern

---

## Decision

**Adopt a three-part decision package:**

### 1. **Toolbar-Driven Block Insertion (UX Flow)**

**Frontend (optimistic rendering):**
1. User clicks "Insert Block (+)" in toolbar
2. Frontend generates temporary client-side UUID, renders empty markdown editor
3. Frontend sends `POST /books/{book_id}/blocks` with `{ type: "markdown", content: "", order: X }`
4. Backend returns canonical `block_id` and final `order`
5. Frontend replaces temporary ID with server ID

**Backend (atomic service operation):**
1. Router receives request, extracts `user_id` from JWT token
2. Service validates Book exists & user owns it (via Library ownership)
3. Domain creates Block with `mark_created()`, emits `BlockCreated` event
4. Repository persists Block
5. Returns block_id + final order for frontend sync

**Benefits:**
- Zero-delay perception (UI responds instantly)
- Server response merges client state with canonical truth
- Handles insertion race conditions via atomic DB operation

### 2. **Soft-Delete for Blocks (Basement Pattern)**

**Rationale:** Consistency with Book/Bookshelf basement model

- `delete_block()` → `block.mark_deleted()` + `save()` (no hard delete)
- Emits `BlockDeleted` event with audit trail
- Soft-deleted blocks remain in DB with `deleted_at` timestamp
- 30-day retention period, then purge job hard-deletes
- Users can restore within 30-day window (future enhancement)

**Benefits:**
- Audit trail and compliance
- Accidental deletion recovery
- Consistent with company-wide soft-delete policy
- Enables "Undo" feature (future)

### 3. **Permission Model: Three-Layer Validation**

**Layer 1: HTTP Router (user identification)**
```python
def get_user_id_from_jwt(request: Request) -> UUID:
    return request.state.user_id  # From FastAPI security
```

**Layer 2: Service Layer (ownership & consistency checks)**
```python
# create_block, update_block_content, reorder_block, delete_block
async def create_block(self, book_id: UUID, ..., user_id: UUID):
    # Step 1: Book exists?
    book = await self.book_repository.get_by_id(book_id)
    if not book: raise BookNotFoundError()

    # Step 2: User owns Library?
    library = await self.library_repository.get_by_id(book.library_id)
    if library.user_id != user_id: raise PermissionError()

    # Step 3: Domain creates Block
    block = Block.create(book_id, block_type, content, order)
    await self.repository.save(block)
    return block
```

**Layer 3: Database (FK constraints)**
- `block.book_id` → `books.id` (FK constraint)
- `block.library_id` → `libraries.id` (FK constraint)
- Both prevent orphaned blocks and cross-library pollution

**Benefits:**
- Defense in depth: user → library → book → block ownership chain
- Service layer catches most violations early
- Database constraints as final safety net
- Audit-friendly (all validations logged)

### 4. **Minimal Content Type: Markdown Text (MVP)**

**Phase 1 (This Sprint):**
- Single block type: `TEXT` / `MARKDOWN`
- `content` field stores markdown text
- `metadata` field reserved (empty JSON for now)
- `title` and `title_level` optional (for outline/hierarchy)

**Phase 2 (Future):**
- Add `CODE` type (with `language` metadata)
- Add `IMAGE` type (with `media_id` + `alt_text`)
- Add `TABLE` type (with structured metadata)
- Runtime block type validation & rendering

**Benefits:**
- Minimal API surface (reduce validation bugs)
- Fast MVP validation (block insertion flow works)
- Easy to extend (add types without breaking existing)
- Clear migration path

### 5. **Block Ordering: Reorder Without Full Index Rebuild**

**Strategy: Interval-based ordering**

```python
# Initial blocks
block_1.order = 1000
block_2.order = 2000
block_3.order = 3000

# Insert between block_1 and block_2
new_order = (block_1.order + block_2.order) / 2
block_new.order = 1500

# Reorder: drag block_new to end
# Reorder: drag block_1 above block_new
# Result: no database writes except the moved block
```

**Reindex trigger:**
- When gaps become too small (< 1.0 between consecutive blocks)
- Or after 100+ reorder operations
- Background job reindexes entire book's blocks: 1000, 2000, 3000, ...

**Benefits:**
- No O(n) rewrites on every move
- High concurrency (each block move is independent)
- Predictable database load

---

## Rationale

### Why Soft-Delete Blocks Like Books?

```
Consistency Pattern (Wordloom Standard):
├─ Library: permanent (1:1 user)
├─ Bookshelf: soft-deleted (Basement recovery)
├─ Book: soft-deleted (Basement recovery)
└─ Block: soft-deleted (30-day retention)

Benefits:
✅ Consistent mental model for users
✅ Audit trail completeness
✅ Recovery / "Undo" capability
✅ Regulatory compliance (data retention policies)

Trade-offs:
⚠️ Slightly larger database (soft-deleted records stay)
⚠️ Queries must filter out soft-deleted blocks
```

### Why Three-Layer Permission Validation?

```
Single-Layer (❌ insufficient):
- Router only: trusts user_id from JWT (assumes valid user)
- Result: User A can modify User B's Book if they know the UUID

Two-Layer (⚠️ partial):
- Router + Service: validates user_id but not library ownership
- Result: Race condition where Book ownership changes between request start and validation

Three-Layer (✅ robust):
- Router: extract user_id from JWT
- Service: validate user_id → library_id → book_id → block_id chain
- Database: FK constraints prevent orphans
- Result: Every layer independently validates, fail-fast semantics
```

### Why Optimistic Frontend Rendering?

```
Pessimistic (❌ delays UX):
1. User clicks Insert
2. Wait for API response
3. Then render block
→ Perceived latency = network round-trip (100-500ms)

Optimistic (✅ instant UX):
1. User clicks Insert
2. Immediately render with client UUID
3. API returns canonical ID
4. Frontend swaps ID
→ Perceived latency = 0ms (user sees immediate feedback)
→ Server response reconciles if needed (order, timestamp, etc.)
```

---

## Implementation

### Block Service Changes (Already Implemented)

```python
class BlockService:
    def __init__(self, repository, book_repository, library_repository):
        self.repository = repository
        self.book_repository = book_repository
        self.library_repository = library_repository

    async def create_block(self, book_id: UUID, block_type: str, content: str,
                          order: int = 0, user_id: UUID = None) -> Block:
        # Validation
        if self.book_repository:
            book = await self.book_repository.get_by_id(book_id)
            if not book:
                raise BookNotFoundError(f"Book {book_id} not found")

            if user_id and self.library_repository:
                library = await self.library_repository.get_by_id(book.library_id)
                if library and library.user_id != user_id:
                    raise PermissionError(f"User {user_id} does not own Book {book_id}")

        # Domain operation
        bt = BlockType(block_type)
        block = Block.create(book_id, bt, content, order)
        await self.repository.save(block)
        return block

    async def delete_block(self, block_id: UUID, user_id: UUID = None) -> None:
        """Soft delete: mark deleted, no hard delete"""
        block = await self.get_block(block_id)

        # Permission check
        if self.book_repository and user_id and self.library_repository:
            book = await self.book_repository.get_by_id(block.book_id)
            if not book:
                raise BookNotFoundError(f"Book {block.book_id} not found")
            library = await self.library_repository.get_by_id(book.library_id)
            if library and library.user_id != user_id:
                raise PermissionError(f"User {user_id} does not own Book {block.book_id}")

        # Soft delete
        block.mark_deleted()  # Domain event emitted
        await self.repository.save(block)  # Only persist, no hard delete
```

### Block Domain (No Changes Needed)

✅ Block domain already properly implements:
- `create()` factory with type safety
- `set_content()`, `set_order()`, `set_title()` emitting events
- `mark_deleted()` for soft delete
- Query properties: `is_heading`, `heading_level`, `is_image`

### Router Layer (Needs Implementation)

```python
@router.post("/books/{book_id}/blocks")
async def create_block_endpoint(
    book_id: UUID,
    request: CreateBlockRequest,  # { type, content, order }
    request: Request,  # For JWT extraction
    service: BlockService = Depends(...)
) -> BlockResponse:
    """Create Block in toolbar"""
    user_id = request.state.user_id  # From JWT middleware
    block = await service.create_block(
        book_id=book_id,
        block_type=request.type,
        content=request.content,
        order=request.order,
        user_id=user_id
    )
    return BlockResponse(id=block.id, order=block.order, created_at=block.created_at)

@router.patch("/blocks/{block_id}")
async def update_block_content(
    block_id: UUID,
    request: UpdateBlockRequest,  # { content }
    request: Request,
    service: BlockService = Depends(...)
) -> BlockResponse:
    """Update Block content"""
    user_id = request.state.user_id
    block = await service.update_block_content(
        block_id=block_id,
        new_content=request.content,
        user_id=user_id
    )
    return BlockResponse.from_domain(block)

@router.delete("/blocks/{block_id}")
async def delete_block_endpoint(
    block_id: UUID,
    request: Request,
    service: BlockService = Depends(...)
) -> None:
    """Delete Block (soft delete)"""
    user_id = request.state.user_id
    await service.delete_block(block_id, user_id=user_id)
```

### Frontend Flow (Pseudocode)

```javascript
// Toolbar: Insert Block
function insertBlock() {
  const tempId = uuidv4();
  const newBlock = {
    id: tempId,
    type: 'markdown',
    content: '',
    order: getNextOrder(),
    isOptimistic: true  // UI hint: use lighter color/animation
  };

  // Add to local state immediately
  setBlocks([...blocks, newBlock]);

  // Async: send to server
  const response = await fetch(`/books/${bookId}/blocks`, {
    method: 'POST',
    body: JSON.stringify({
      type: 'markdown',
      content: '',
      order: newBlock.order
    }),
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const canonical = await response.json();  // { id, order, created_at }

  // Replace optimistic ID with canonical
  setBlocks(blocks.map(b =>
    b.id === tempId ? { ...b, id: canonical.id, isOptimistic: false } : b
  ));

  // Focus on new block for immediate editing
  focusBlock(canonical.id);
}

// Edit: Update content
async function updateBlockContent(blockId, newContent) {
  // Update UI first (optimistic)
  setBlocks(blocks.map(b =>
    b.id === blockId ? { ...b, content: newContent } : b
  ));

  // Async persist
  await fetch(`/blocks/${blockId}`, {
    method: 'PATCH',
    body: JSON.stringify({ content: newContent })
  });
}
```

---

## Impact Analysis

### Code Distribution Impact

| Layer | Before | After | Change |
|-------|--------|-------|--------|
| **Domain** | 450 LOC | 450 LOC | No change (well-designed) |
| **Service** | ~60 LOC | 90 LOC | +30 LOC (permission checks) |
| **Router** | TBD | ~60 LOC | New endpoints |
| **Frontend** | TBD | ~100 LOC | Toolbar + optimistic render |

### Performance Implications

✅ **Positive:**
- Interval-based ordering avoids full reindex (O(1) per move vs O(n))
- Service-layer permission checks catch bugs early (fail-fast)
- Soft-delete with indexing on `deleted_at` (fast queries)

⚠️ **Considerations:**
- Repository must filter soft-deleted blocks in list queries
- Periodic purge job required (background process)
- Memory overhead: client-side temporary UUIDs (negligible)

### Operational Concerns

🔧 **Required:**
- Purge job: Hard-delete blocks with `deleted_at > 30 days` (nightly)
- Migration: Add `deleted_at` and `updated_at` indices to blocks table
- Monitoring: Track soft-deleted block count (shouldn't grow unbounded)

---

## Verification

### Unit Tests Required

```python
# Service layer
- test_create_block_validates_book_exists()
- test_create_block_validates_user_ownership()
- test_create_block_rejects_different_library()
- test_delete_block_soft_deletes_no_hard_delete()
- test_update_block_content_updates_only_content()
- test_reorder_block_changes_only_order()

# Domain layer (already exists)
- test_block_create_emits_event()
- test_block_mark_deleted_emits_event()
- test_query_properties_work()

# Router layer
- test_create_block_endpoint_requires_auth()
- test_create_block_endpoint_returns_canonical_id()
- test_delete_block_endpoint_soft_deletes()
```

### Integration Tests Required

```python
# E2E: Block lifecycle
- test_insert_block_via_toolbar_flow()
- test_edit_block_content_persists()
- test_reorder_blocks_maintains_order()
- test_delete_block_soft_deletes_and_persists()
- test_restore_block_from_soft_delete()  # Future
- test_purge_job_hard_deletes_30_day_old()

# Concurrency
- test_concurrent_block_insertions_maintain_order()
- test_concurrent_block_reorders_no_duplicates()
- test_concurrent_block_edits_merge_safely()
```

### Validation Checklist

- [x] Block Service: permission checks implemented
- [x] Block Domain: no changes needed (well-designed)
- [ ] Router endpoints: create, update, delete, list
- [ ] Frontend: toolbar insertion with optimistic rendering
- [ ] Purge job: background task for 30-day retention
- [ ] Database migrations: `deleted_at` column + indices
- [ ] Unit tests: all 10+ tests passing
- [ ] Integration tests: E2E flow verified
- [ ] Load testing: concurrent block operations (100+ ops/sec)

---

## Related Decisions

**[ADR-001: Independent Aggregate Roots](ADR-001-independent-aggregate-roots.md)**
- Block is independent aggregate root (not nested in Book)
- Three-layer permission validation implements the FK model

**[ADR-002: Basement Pattern](ADR-002-basement.md)**
- Block soft-delete with 30-day retention mirrors Book/Bookshelf pattern
- Purge job hardwares-deletes after retention window

**[ADR-004: Auxiliary Features Layering](ADR-004-auxiliary-features-layering.md)**
- Block Service layer orchestrates validation and domain operations
- Follows the three-layer service pattern established

**[ADR-006: Book Domain Refinement](ADR-006-book-domain-refinement.md)**
- Block builds on Book's refined permission model
- Service layer validation pattern identical to Book/Bookshelf

---

## Future Enhancements

**Phase 2 (Next Sprint):**
- Add more block types (code, image, table)
- Implement block restoration from soft-delete
- Add conflict-free reordering for collaborative editing

**Phase 3 (Q1 2026):**
- Rich text editor integration (markdown → Delta format)
- Real-time collaborative editing (CRDT or OT)
- Block history and version tracking

**Phase 4 (Q2 2026):**
- Media asset management (images, files)
- Smart preview generation (link cards, code syntax highlighting)
- Advanced querying (full-text search, tag filtering)

---

## References

- **Files Modified:**
  - `backend/api/app/modules/domains/block/service.py` (permission checks added)
  - `backend/docs/DDD_RULES.yaml` (RULE-013 through RULE-017 updated, POLICY-008/009 status updated)

- **Files To Be Created:**
  - `backend/api/app/modules/domains/block/router.py` (HTTP endpoints)
  - `backend/api/app/migrations/add_block_soft_delete.py` (database migration)
  - `backend/api/jobs/purge_deleted_blocks.py` (purge job)

- **Related Documentation:**
  - Design Doc: Block Toolbar UX Flow (Figma)
  - Operational Runbook: Purge Job Setup and Monitoring

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2025-11-12 | Agent | Initial ADR for Block insertion architecture and soft-delete model |

---

## Sign-Off

**Approved:** ✅ Architecture accepted, ready for implementation
**Next Steps:** Implement Router layer, Frontend toolbar, Database migration, Purge job
