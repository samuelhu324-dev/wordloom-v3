# ADR-053: Wordloom Core Database Schema Design

## Status
✅ ACCEPTED (2025-11-15)
✅ IMPLEMENTED & VERIFIED (2025-11-15)
   - Database: `wordloom` created
   - Schema: 11 tables initialized
   - Extensions: uuid-ossp, pg_trgm, btree_gin enabled
   - Verification: All constraints and indexes created

## Context

Wordloom v3 requires a comprehensive database schema that:
1. Supports DDD aggregate roots (Library → Bookshelf → Book → Block)
2. Implements Hexagonal Architecture with clear domain boundaries
3. Enables soft-delete recovery patterns (Basement, Paperballs, Vault)
4. Supports cross-entity features (Tags, Media, Full-text search)
5. Maintains audit trails (Chronicle)
6. Provides multi-tenant isolation (user_id)

## Decision

We adopt a **PostgreSQL schema** with the following design principles:

### 1. Aggregate Root Hierarchy

```
Library (AggregateRoot)
├── Bookshelf (Child container, max 100 per library)
│   ├── Books (Independent AR, soft-delete to Basement)
│   │   └── Blocks (Value objects, soft-delete to Paperballs)
├── Tags (Global, cross-entity)
├── Media (Global asset library)
└── Chronicle (Audit trail)
```

### 2. Core Tables (7)

#### Table 1: `libraries`
- **Purpose**: User's single library (RULE-001)
- **Key Constraints**:
  - `UNIQUE(user_id)` - exactly 1 library per user
  - `soft_deleted_at` - Basement concept (BASEMENT-001)
- **Indexes**: user_id, soft_deleted_at
- **Triggers**: Auto-creates Basement bookshelf on insert

#### Table 2: `bookshelves`
- **Purpose**: Data containers within library (RULE-004, RULE-006)
- **Key Constraints**:
  - `UNIQUE(library_id, name)` - unique names per library
  - `is_basement` - special bookshelf for soft-deleted books
  - `status` - ACTIVE|ARCHIVED|DELETED
  - Max 100 per library (enforced in application layer)
- **Indexes**: library_id, is_basement, status
- **Special**: Automatically created Basement bookshelf on library creation

#### Table 3: `books`
- **Purpose**: Independent aggregate root (RULE-009)
- **Key Constraints**:
  - `UNIQUE(library_id, bookshelf_id, title)` - implicit (enforced via app)
  - `soft_deleted_at` - Basement recovery (BASEMENT-002)
  - `deleted_from_shelf_id` - records original bookshelf
  - `status` - ACTIVE|READING|COMPLETED|ON_HOLD
- **Indexes**: bookshelf_id, library_id, soft_deleted_at, status
- **Properties**: title, author, isbn, priority, urgency, reading_progress

#### Table 4: `blocks`
- **Purpose**: Smallest content unit (RULE-013, RULE-014)
- **Key Constraints**:
  - `sort_key DECIMAL(20,10)` - Fractional Index for infinite reordering (RULE-015)
  - `soft_deleted_at` - Paperballs recovery (PAPERBALLS-POS-001)
  - `deleted_prev_block_id, deleted_next_block_id` - recovery links
  - `deleted_section_path` - hierarchical recovery info
- **Indexes**: book_id, sort_key (composite), soft_deleted_at
- **Types**: text|heading|code|image|quote|list|table|divider|latex|mermaid|custom
- **Properties**: content, language (for code), collapsed flag

#### Table 5: `tags`
- **Purpose**: Global cross-entity tags (RULE-018, RULE-019, RULE-020)
- **Key Constraints**:
  - `UNIQUE(user_id, name)` - multi-tenant isolation
  - `parent_tag_id` - hierarchical tags (RULE-020)
  - `usage_count` - performance cache (POLICY-010)
- **Indexes**: user_id, parent_tag_id, soft_deleted_at
- **Properties**: color, icon_emoji, description

#### Table 6: `media`
- **Purpose**: Global asset library (POLICY-009, POLICY-010)
- **Key Constraints**:
  - `UNIQUE(storage_key)` - prevents duplicate uploads
  - `state` - ACTIVE|TRASH (VAULT-001)
  - `trash_at` - timestamp when moved to trash
  - `purge_at` - 30-day retention before permanent delete
- **Indexes**: user_id, state, trash_at, storage_key
- **Properties**: width, height (images), duration_ms (videos)

#### Table 7: `chronicle_events`
- **Purpose**: Complete audit trail (CHRONICLE-001)
- **Key Columns**: entity_type, entity_id, action, data_snapshot, change_details
- **Indexes**: user_id, entity_type, entity_id, created_at

### 3. Association Tables (3)

| Table | Purpose | Constraint |
|-------|---------|-----------|
| `block_tags` | Block ↔ Tag many-to-many | CASCADE on delete |
| `book_tags` | Book ↔ Tag many-to-many | CASCADE on delete |
| `media_associations` | Media ↔ Entity binding | UNIQUE per media+entity |

### 4. Search Support

**Table**: `search_index`
- Denormalized FTS index (SEARCH-001, SEARCH-002)
- Contains title + content_text + search_vector (tsvector)
- Maintained by triggers (planned in Phase B)
- GIN index on search_vector for fast full-text search

### 5. Soft-Delete Pattern

All domain entities support soft deletion:

```sql
-- Active records
SELECT * FROM books WHERE soft_deleted_at IS NULL;

-- Basement (soft-deleted)
SELECT * FROM books WHERE soft_deleted_at IS NOT NULL;

-- Immediate hard-delete via Vault (30-day retention)
DELETE FROM media WHERE purge_at < NOW();
```

### 6. Trigger Strategy

| Trigger | Function | When |
|---------|----------|------|
| `update_*_timestamp` | Auto-update `updated_at` | BEFORE UPDATE on all tables |
| `create_basement_trigger` | Auto-create Basement bookshelf | AFTER INSERT on libraries |

### 7. Indexes

**Performance Indexes:**
- user_id (multi-tenant filtering)
- foreign keys (join optimization)
- sort_key composite (block ordering)
- soft_deleted_at (active/basement queries)
- status (state filtering)
- search_vector (full-text search, GIN)

**Total Indexes**: 30+ (detailed in schema.sql)

### 8. Constraints

**Data Integrity:**
- Foreign key cascading (parent delete → cascade to children)
- NOT NULL on critical fields
- CHECK constraints on enums (block_type, state, status)
- CHECK constraints on ranges (reading_progress 0-100)
- Color format validation (#RRGGBB regex)

### 9. Views

| View | Purpose |
|------|---------|
| `active_books` | Books not soft-deleted |
| `active_blocks` | Blocks not soft-deleted |
| `basement_books` | Soft-deleted books for recovery UI |

## Database Setup

### Creation
```bash
# Create database
createdb -h 127.0.0.1 -p 5433 -U postgres -E UTF8 wordloom

# Execute schema
psql postgresql://postgres:pgpass@127.0.0.1:5433/wordloom -f backend/api/app/migrations/001_create_core_schema.sql

# Initialize with demo data
python backend/api/app/migrations/init_database.py --action all
```

### Connection String
```
DATABASE_URL=postgresql://postgres:pgpass@127.0.0.1:5433/wordloom
```

### Verification
```bash
# Check tables
psql ... -c "\dt"

# Check indexes
psql ... -c "\di"

# Check triggers
psql ... -c "\dy"
```

## Mapping to RULES

### DDD_RULES.yaml Compliance

| Rule | Table(s) | Constraint |
|------|----------|-----------|
| RULE-001 | libraries | UNIQUE(user_id) |
| RULE-004 | bookshelves | Max 100 per library (app layer) |
| RULE-006 | bookshelves | UNIQUE(library_id, name) |
| RULE-009 | books | Independent AR with library_id FK |
| RULE-015 | blocks | sort_key DECIMAL(20,10) for Fractional Index |
| RULE-018 | tags | Global tags |
| RULE-020 | tags | parent_tag_id for hierarchy |
| BASEMENT-001 | libraries | soft_deleted_at column |
| BASEMENT-002 | books | soft_deleted_at + deleted_from_shelf_id |
| PAPERBALLS-POS-001/002/003 | blocks | deleted recovery columns |
| VAULT-001 | media | 30-day purge_at retention |

### HEXAGONAL_RULES.yaml Compliance

**Port Definitions**: Repository interfaces map 1:1 to tables
- ILibraryRepository ↔ libraries
- IBookshelfRepository ↔ bookshelves
- IBookRepository ↔ books
- IBlockRepository ↔ blocks
- ITagRepository ↔ tags
- IMediaRepository ↔ media

**Adapter Implementations**: SQLAlchemy ORM models
- backend/api/app/infra/orm/library.py
- backend/api/app/infra/orm/book.py
- etc.

### VISUAL_RULES.yaml Compliance

**Frontend Data Types**: Align with schema
- soft_deleted_at → show Basement/Paperballs icons in UI
- block_type → render different block editors
- is_basement → hide from normal navigation
- status → filter in queries

## Migration Strategy

### Phase A: Week 1 (Current)
✅ Create clean schema without old data
✅ Verify all constraints and triggers work
✅ Insert demo data for testing

### Phase B: Week 2 (Optional)
- Create migration scripts for old WordLoom data
- Map orbit_notes → books, blocks_json → blocks
- Handle data type conversions (UUID, Fractional Index)
- Validate all constraints post-migration

### Phase C: Future (Post-MVP)
- Alembic migration system for subsequent schema changes
- Database backup/restore procedures
- Performance tuning (partition large tables if needed)

## Performance Considerations

1. **Denormalization**: library_id in books table for faster queries
2. **Soft Delete Filtering**: Always check soft_deleted_at in WHERE clauses
3. **Fractional Index**: DECIMAL(20,10) supports up to 100 billion reorderings
4. **Index Coverage**: Composite indexes on frequently joined columns
5. **FTS Search**: Denormalized search_index table (updated by triggers)

## Constraints & Limits

| Constraint | Limit | Enforced By |
|-----------|-------|------------|
| Libraries per user | 1 | UNIQUE constraint |
| Bookshelves per library | 100 | Application layer |
| Books per bookshelf | Unlimited | None |
| Blocks per book | Unlimited | None |
| Tag hierarchy depth | Unlimited | None |
| Trash retention (media) | 30 days | Application cleanup job |

## Consequences

### Positive ✅
- Clear domain boundaries (tables ≈ aggregate roots)
- Soft-delete recovery pattern built-in (Basement/Paperballs/Vault)
- Multi-tenant ready (user_id isolation)
- Audit trail support (chronicle_events)
- Full-text search capable (search_index)
- Foreign key integrity maintained

### Negative ⚠️
- Denormalization increases write complexity
- Fractional Index updates can be expensive (need batching)
- Search index maintenance required (triggers + manual sync)
- Schema modifications require data migration

## Alternatives Considered

1. **NoSQL (MongoDB)**
   - ❌ Rejected: DDD requires strict relationships, ACID transactions needed

2. **Nested Documents (JSONB)**
   - ⚠️ Partial: Could nest blocks as JSONB in books, but hurts searchability

3. **EAV Model**
   - ❌ Rejected: Too complex for this domain, performance poor

## References

- **Backend**: DDD_RULES.yaml, HEXAGONAL_RULES.yaml
- **Frontend**: VISUAL_RULES.yaml (data type mappings)
- **Implementation**: backend/api/app/migrations/001_create_core_schema.sql
- **Init Script**: backend/api/app/migrations/init_database.py
- **ORM Models**: backend/api/app/infra/orm/*.py (WIP)
- **Deletion Pattern**: ADR-038-deletion-recovery-unified-framework.md
- **Search**: ADR-050-search-module-design.md

## Sign-Off

- **Author**: Architecture Team
- **Date**: 2025-11-15
- **Status**: ✅ ACCEPTED
- **Next**: Phase A execution (this week)
