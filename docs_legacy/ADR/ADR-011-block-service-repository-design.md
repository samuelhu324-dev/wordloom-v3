# ADR-011: Block Service & Repository Design (Fractional Index + HEADING BlockType)

**Status:** Accepted
**Date:** 2025-11-12
**Author:** Architecture Team
**Related ADR:** ADR-001, ADR-008, ADR-009, ADR-010

## Problem Statement

The Block domain requires revolutionary optimizations for content management:

1. **Fractional Index Ordering** (RULE-015-REVISED): O(1) drag/drop instead of O(n) batch recomputation
2. **HEADING as BlockType** (RULE-013-REVISED): Eliminate title_text/title_level fields, use type system
3. **Type-Specific Creation** (RULE-013): Different block types need different factory methods
4. **Soft Delete Pattern** (POLICY-008): Mark deleted, not hard delete (30-day purge)
5. **Exception Translation**: Database constraints converted to Domain exceptions
6. **Comprehensive Logging**: Operation tracking for debugging

## Architecture Decision

### 1. Fractional Index Strategy (O(1) Drag/Drop)

**Problem:** Traditional integer ordering requires O(n) batch updates when reordering

**Solution:** Use Decimal(19,10) with fractional indexing algorithm

```sql
-- Database schema change
order: INTEGER → NUMERIC(19, 10)  -- Supports fractional values with 10 decimal places
```

#### Algorithm: Insert Between Two Blocks

```python
# Get left and right neighbors
left_order = Decimal('10.0')   # Order of block before insertion point
right_order = Decimal('20.0')  # Order of block after insertion point

# Calculate middle value
new_order = (left_order + right_order) / 2  # = 15.0

# Result: Single INSERT, no batch updates
```

#### Example Sequence: Multiple Drags

```
Initial state:
Block A: order=10.0
Block B: order=20.0

1st drag (insert between A and B):
Block C: order = (10.0 + 20.0) / 2 = 15.0

2nd drag (insert between A and C):
Block D: order = (10.0 + 15.0) / 2 = 12.5

3rd drag (insert between D and C):
Block E: order = (12.5 + 15.0) / 2 = 13.75

10th+ drag: Precision limit reached (10 decimal places)
→ Trigger background renormalization job
→ Reset to integers: 10, 20, 30, ...
```

#### Precision Handling

```python
# If decimal places exceed 10, execute renormalization (background job)
def normalize_block_order(book_id: UUID):
    """
    Reset all block orders to clean integer multiples

    Executed when:
    - Decimal precision exceeds 10 places
    - Manual maintenance trigger
    """
    blocks = await repo.get_by_book_id(book_id)  # Already sorted by order

    for i, block in enumerate(blocks):
        block.order = Decimal(str((i + 1) * 10))  # 10, 20, 30, ...
        await repo.save(block)
```

#### Benefits

- **O(1) Operations**: Single reorder updates only one block, not all siblings
- **Concurrent Safety**: Multiple drag operations don't conflict
- **Unlimited Depth**: Theoretically infinite nesting (10 decimal places ≈ 10^10 drag operations)
- **Used in Production**: Google Firestore, Notion, Obsidian all use this pattern

### 2. HEADING as BlockType (Simplified Type System)

**Problem:** title_text and title_level on every block adds complexity

**Solution:** HEADING becomes a first-class BlockType

#### Before (Phase 7)

```python
class Block:
    type: BlockType = TEXT  # Always has generic type
    content: str
    title_text: Optional[str] = None  # Extra field
    title_level: Optional[int] = None  # Extra field

    def set_title(text: str, level: int):  # Extra method
        ...
    def remove_title(self):  # Extra method
        ...
```

#### After (Phase 8)

```python
class BlockType(Enum):
    TEXT = "text"
    HEADING = "heading"      # ← Now a type, not a field
    CODE = "code"
    IMAGE = "image"
    QUOTE = "quote"
    LIST = "list"
    DIVIDER = "divider"

class Block:
    type: BlockType           # HEADING replaces title concept
    content: str
    heading_level: Optional[int] = None  # Only set if type==HEADING

    # No set_title() / remove_title() methods
```

#### Benefits

- **Type Clarity**: Block type is self-documenting (HEADING ≠ TEXT)
- **Simpler Logic**: No optional field checks
- **UI Rendering**: Can dispatch on type directly
- **Extensibility**: Add new types (DIVIDER, CHECKBOX) without adding fields

### 3. Type-Specific Factory Methods

Replace generic `create()` with specialized methods

```python
# Before
block = Block.create(book_id, BlockType.TEXT, "content", order=10)
block = Block.create(book_id, BlockType.HEADING_1, "title", order=20)
block = Block.create(book_id, BlockType.CODE, "code", order=30)

# After
text_block = Block.create_text(book_id, "content", order=10)
heading_block = Block.create_heading(book_id, "title", level=2, order=20)
code_block = Block.create_code(book_id, "code", language="python", order=30)
image_block = Block.create_image(book_id, order=40)
quote_block = Block.create_quote(book_id, "quote text", order=50)
list_block = Block.create_list(book_id, "- item 1\n- item 2", order=60)
```

#### Service Layer Methods

Corresponding type-specific methods in Service:

```python
class BlockService:
    async def create_text_block(book_id, content, order, user_id):
        ...

    async def create_heading_block(book_id, content, level, order, user_id):
        ...

    async def create_code_block(book_id, content, language, order, user_id):
        ...

    async def create_image_block(book_id, order, user_id):
        ...

    # Fractional index convenience method
    async def reorder_block_between(book_id, before_order, after_order, user_id):
        # Calculates: new_order = (before_order + after_order) / 2
        ...
```

### 4. Four-Layer Service Architecture (extends ADR-008/ADR-009/ADR-010)

```
Layer 1: Validation
├─ Book existence check (FK validation)
├─ Heading level validation (1-3 for HEADING type)
├─ Permission check via Library ownership
└─ Fractional index validity

Layer 2: Domain Logic
├─ Call Domain Factory: Block.create_text(), create_heading(), etc.
├─ Call Domain Methods: set_content(), set_order_fractional()
├─ Extract Domain Events from aggregate
└─ Validate all invariants

Layer 3: Persistence
├─ Repository.save() with Decimal order mapping
├─ Handle IntegrityError → BlockException translation
└─ Logging at persistence level

Layer 4: Event Publishing
├─ Collect block.events (BlockCreated, BlockReordered, etc.)
├─ Publish to EventBus asynchronously
└─ Exception isolation (failures don't break main flow)
```

### 5. Soft Delete Query Filtering

```python
# Default filter: soft_deleted_at IS NULL
async def get_by_book_id(book_id):
    stmt = (
        select(BlockModel)
        .where(BlockModel.book_id == book_id)
        .where(BlockModel.soft_deleted_at.is_(None))  # ← Auto-exclude deleted
        .order_by(BlockModel.order.asc())  # Fractional index order
    )
    return ...

# Explicit query for deleted blocks (recovery)
async def get_deleted_blocks(book_id):
    stmt = (
        select(BlockModel)
        .where(BlockModel.book_id == book_id)
        .where(BlockModel.soft_deleted_at.isnot(None))  # Only deleted
        .order_by(BlockModel.soft_deleted_at.desc())
    )
    return ...
```

### 6. Database Schema Migration

```sql
-- Remove title columns
ALTER TABLE blocks DROP COLUMN title_text;
ALTER TABLE blocks DROP COLUMN title_level;

-- Add heading_level (only for HEADING blocks)
ALTER TABLE blocks ADD COLUMN heading_level INTEGER NULL;

-- Rename block_type → type
ALTER TABLE blocks RENAME COLUMN block_type TO type;

-- Change order to Decimal for fractional indexing
ALTER TABLE blocks ALTER COLUMN order TYPE NUMERIC(19, 10);

-- Add soft delete support
ALTER TABLE blocks ADD COLUMN soft_deleted_at TIMESTAMP WITH TIME ZONE NULL;

-- Create index for soft delete queries
CREATE INDEX idx_blocks_soft_deleted ON blocks(soft_deleted_at) WHERE soft_deleted_at IS NULL;
CREATE INDEX idx_blocks_order ON blocks(order);  -- For fractional ordering
```

## Code Examples

### Creating Different Block Types

```python
# Text block
text = await service.create_text_block(
    book_id=uuid(...),
    content="This is plain text",
    order=Decimal('10.0'),
    user_id=user_id
)

# Heading block
heading = await service.create_heading_block(
    book_id=uuid(...),
    content="Chapter 1: Introduction",
    level=1,  # H1
    order=Decimal('20.0'),
    user_id=user_id
)

# Code block
code = await service.create_code_block(
    book_id=uuid(...),
    content="def hello():\n    print('world')",
    language="python",
    order=Decimal('30.0'),
    user_id=user_id
)

# Image block
image = await service.create_image_block(
    book_id=uuid(...),
    order=Decimal('40.0'),
    user_id=user_id
)
```

### Drag/Drop Reordering (O(1))

```python
# Get neighbors
blocks = await service.list_blocks(book_id)
# blocks[0].order = 10.0
# blocks[1].order = 20.0
# blocks[2].order = 30.0

# Drag blocks[2] between blocks[0] and blocks[1]
new_order = (blocks[0].order + blocks[1].order) / 2  # 15.0

# Single operation, O(1)
await service.reorder_block_between(
    block_id=blocks[2].id,
    before_order=Decimal('10.0'),
    after_order=Decimal('20.0'),
    user_id=user_id
)
```

### Type Checking

```python
# Query and filter by type
blocks = await service.list_blocks(book_id)

for block in blocks:
    if block.type == BlockType.HEADING:
        print(f"Heading (H{block.heading_level}): {block.content}")
    elif block.type == BlockType.CODE:
        print(f"Code: {block.content}")
    else:
        print(f"{block.type.value}: {block.content}")
```

## Comparison: Old vs New

| Aspect | Old (Phase 7) | New (Phase 8) |
|--------|---------------|--------------|
| **Order Type** | `INT` | `NUMERIC(19,10)` (Decimal) |
| **Reorder Cost** | O(n) batch updates | O(1) single update |
| **Title Concept** | Fields: title_text, title_level | Type: BlockType.HEADING |
| **Heading Levels** | 4 BlockTypes (HEADING_1-3) | 1 BlockType (HEADING) + level field |
| **Factory Method** | Generic `create(type, content)` | Type-specific: `create_text()`, `create_heading()` |
| **Soft Delete Filtering** | Manual WHERE clause | Auto-applied in Repository |
| **Database Columns** | 22 columns | 20 columns (removed title_text, title_level) |

## Migration Path

1. **Create new blocks table** with Decimal order and HEADING type
2. **Migrate existing blocks** from old schema:
   - TEXT blocks stay as TEXT
   - HEADING_1/2/3 → HEADING (with level in heading_level)
   - ORDER INT → NUMERIC(19,10)
3. **Update application code**:
   - Domain: Remove set_title(), add create_heading(), change order type
   - Service: Add type-specific methods, update reorder logic
   - Repository: Remove title mapping, add heading_level support
4. **Run validation** to ensure no data loss
5. **Deploy** with feature flag (if needed)

## Rejected Alternatives

### Nested Markers (Tree Structure)
- **Why Rejected**: Complex queries, slow traversal, not needed for Wordloom
- **Chosen**: Flat structure with fractional indexing

### Keeping title_text/title_level
- **Why Rejected**: Optional fields on every block add complexity
- **Chosen**: HEADING as dedicated BlockType

### Integer Order with Batch Recomputation
- **Why Rejected**: O(n) performance, contention under concurrent drag
- **Chosen**: Fractional indexing O(1)

## Testing Strategy

### Unit Tests
- Fractional index calculation edge cases
- HEADING level validation (1-3)
- Type-specific factory methods
- Soft delete filtering

### Integration Tests
- Drag/drop scenarios with multiple reorders
- Type-specific creation and querying
- Cross-type migrations
- Soft delete and recovery

### Performance Tests
- Benchmark drag/drop: O(1) vs O(n)
- Measure query performance on large block sets
- Verify index usage

## Rollback Plan

If issues arise:
1. Keep old blocks table temporarily
2. Parallel write to both tables during migration
3. If rollback needed: revert to old table, drop new table

## Future Enhancements

- Metadata JSON field for type-specific data (code language, image alt text, etc.)
- Block grouping/nesting (optional, if needed)
- Hierarchical heading detection and tree building (query-time)
- Fractional index rebalancing algorithm optimization

## References

- [Fractional Indexing Notion](https://www.notion.so/Fractional-Indexing)
- [Google Firestore Array Operations](https://firebase.google.com/docs/firestore/manage-data/arrays)
- ADR-001: Independent Aggregate Roots
- ADR-008: Library Service & Repository Design
- ADR-009: Bookshelf Service & Repository Design
- ADR-010: Book Service & Repository Design
