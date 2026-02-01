# ADR-025: Tag Service, Repository & API Layer Design

**Date**: November 13, 2025
**Status**: ACCEPTED ✅
**Version**: 1.0
**Context**: Phase 2 - Tag Module Implementation
**Related**: ADR-020 (Bookshelf Router/Schemas/Exceptions), ADR-021 (Book Router/Schemas/Exceptions), ADR-022 (Block Router/Schemas/Exceptions)

---

## Executive Summary

Tag module implementation: **0 → 8.5/10 maturity**

This ADR documents the complete implementation of the Tag module, including domain layer (AggregateRoot), service business logic, repository persistence, exceptions hierarchy, Pydantic schemas, and FastAPI router. The Tag module manages global tagging system with support for:
- Multi-entity associations (Bookshelf/Book/Block completely independent)
- Hierarchical tag structures (multi-level categorization)
- Soft delete with audit preservation
- Menu bar integration (usage statistics)
- Full-text search and autocomplete

**Key Achievement**: Complete separation of concerns - Tag associations to different entity types are fully independent (no automatic sync), enabling flexible UI layer presentation.

---

## Problem Statement

### Current State (Before Implementation)

Tag module was in "planned" state with skeleton files:
- domain.py: empty
- service.py: empty
- repository.py: empty
- models.py: empty (except import stubs)
- exceptions.py: basic structure only
- schemas.py: empty
- router.py: empty

### Design Challenges Addressed

1. **Multi-Entity Association Model**
   - Bookshelf tags should NOT automatically propagate to Book tags
   - TagAssociation uses denormalized entity_type + entity_id (not separate tables)
   - Query patterns: "get all tags for a Book" vs. "get all Books with this tag"

2. **Hierarchical Structure**
   - Support multi-level tag categorization (0=top, 1=sub, 2=sub-sub)
   - Prevent cycles (A cannot have itself as ancestor)
   - Maximum 3 depth levels (configurable)
   - Efficient tree queries (parent_tag_id + level indexes)

3. **Soft Delete Complexity**
   - Deleted tags should not appear in queries
   - Associations are preserved (for audit trail, potential restore)
   - Allow tag name reuse after soft delete (not globally unique, but unique among active)

4. **Usage Statistics Caching**
   - usage_count field cached for efficient sorting (menu bar)
   - Updated on every associate/disassociate
   - Async purge jobs later can rebuild if needed

---

## Architecture Decision

### Core Principles

1. **Independent Associations (NOT Hierarchical)**
   ```
   Book #1 tagged with "Python"    ✓
   Bookshelf #1 tagged with "Important"  ✓
   → NO automatic sync, completely independent
   UI layer can choose to display both or separate
   ```

2. **Multi-Level Hierarchy Support**
   ```
   Technology (level=0)
   ├─ Python (level=1, parent=Technology)
   │  ├─ Django (level=2, parent=Python)
   └─ JavaScript (level=1, parent=Technology)
   ```

3. **Soft Delete Pattern**
   ```
   deleted_at IS NULL → active tags (shown in menus, queries)
   deleted_at IS NOT NULL → archived tags (preserved for associations)
   All repository queries auto-filter deleted_at IS NULL
   restore() endpoint to undelete
   ```

4. **DDD Separation**
   - Domain: Tag AggregateRoot + TagAssociation ValueObject (no infra imports)
   - Service: Business logic orchestration (RULE-018/019/020 enforcement)
   - Repository: Persistence abstraction + query patterns
   - API: HTTP endpoints + validation

---

## Detailed Implementation

### 1. Domain Layer (RULE-018/019/020 Enforcement)

**Location**: `backend/api/app/modules/tag/domain.py`

#### 1.1 TagAssociation Value Object

```python
@dataclass(frozen=True)
class TagAssociation(ValueObject):
    """Immutable link between Tag and entity"""
    tag_id: UUID
    entity_type: EntityType  # BOOKSHELF | BOOK | BLOCK
    entity_id: UUID
    created_at: datetime

    # UNIQUE constraint: (tag_id, entity_type, entity_id)
```

**Rationale**:
- Immutable: associations don't update, only create/delete
- Denormalized entity reference: avoids separate tables per entity type
- Enables efficient reverse lookup: "all entities with tag X"

#### 1.2 Tag Aggregate Root

```python
@dataclass
class Tag(AggregateRoot):
    id: UUID
    name: str               # UNIQUE, 1-50 chars (RULE-018)
    color: str              # Hex format: #RRGGBB or #RRGGBBAA
    icon: Optional[str]     # Lucide icon name
    description: Optional[str]

    # Hierarchy (RULE-020)
    parent_tag_id: Optional[UUID]
    level: int = 0          # 0=toplevel, 1=sub, 2=sub-sub

    # Statistics
    usage_count: int = 0    # Cached count of TagAssociations

    # Lifecycle
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]  # Soft delete marker

    _events: List[DomainEvent]  # Domain events (uncaught)
```

**Factories**:

```python
@staticmethod
def create_toplevel(name, color, icon=None, description=None) -> Tag:
    """Create top-level tag (level=0, parent_tag_id=None)"""

@staticmethod
def create_subtag(parent_tag_id, name, color, icon=None, parent_level=0) -> Tag:
    """Create hierarchical sub-tag (level=parent_level+1)"""
```

**Methods**:

```python
def rename(new_name: str) -> None
def update_color(new_color: str) -> None
def update_icon(new_icon: Optional[str]) -> None
def update_description(new_description: Optional[str]) -> None

def soft_delete() -> None
def restore() -> None
def is_deleted() -> bool

def associate_with_entity(entity_type, entity_id) -> TagAssociation
def disassociate_from_entity(entity_type, entity_id) -> None

def increment_usage(by=1) -> None
def decrement_usage(by=1) -> None
```

**Domain Events** (6 total):

1. `TagCreated`: tag_id, name, color, is_toplevel
2. `TagRenamed`: tag_id, old_name, new_name
3. `TagColorChanged`: tag_id, old_color, new_color
4. `TagDeleted`: tag_id
5. `TagAssociatedWithEntity`: tag_id, entity_type, entity_id
6. `TagDisassociatedFromEntity`: tag_id, entity_type, entity_id

---

### 2. Exception Hierarchy (13 Exceptions)

**Location**: `backend/api/app/modules/tag/exceptions.py`

**HTTP Mapping**:

| Exception | Status | Rule | Use Case |
|-----------|--------|------|----------|
| TagNotFoundError | 404 | RULE-018 | Tag ID not found |
| TagAlreadyExistsError | 409 | RULE-018 | Duplicate name |
| TagInvalidNameError | 422 | RULE-018 | Name validation failed |
| TagInvalidColorError | 422 | RULE-018 | Color format invalid |
| TagInvalidHierarchyError | 422 | RULE-020 | Parent not found / cycle / max depth exceeded |
| TagAlreadyAssociatedError | 409 | RULE-019 | Association already exists |
| TagAssociationNotFoundError | 404 | RULE-019 | Association to remove not found |
| TagAlreadyDeletedError | 409 | RULE-018 | Tag already soft-deleted |
| TagOperationError | 500 | - | Generic operation failure |
| TagRepositoryException | 500 | - | Database operation failure |

**Key Feature**: Structured error responses

```python
{
    "code": "TAG_INVALID_NAME",
    "message": "Invalid tag name: Tag name must be <= 50 characters",
    "details": {"reason": "Too long", "name": "VeryLongTagNameThatExceedsLimit"}
}
```

---

### 3. ORM Models (2 Tables)

**Location**: `backend/api/app/modules/tag/models.py`

#### 3.1 TagModel (SQLAlchemy)

```python
class TagModel(Base):
    __tablename__ = "tags"

    # Primary key
    id = Column(UUID, primary_key=True, default=uuid4)

    # Core (RULE-018)
    name = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(9), nullable=False)  # #RRGGBB or #RRGGBBAA
    icon = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # Hierarchy (RULE-020)
    parent_tag_id = Column(UUID, ForeignKey("tags.id"), nullable=True)
    level = Column(Integer, nullable=False, default=0, index=True)

    # Statistics
    usage_count = Column(Integer, nullable=False, default=0, index=True)

    # Lifecycle
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)  # Soft delete

    # Relationships
    tag_associations = relationship("TagAssociationModel", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name_active"),
        Index("ix_tags_parent_level", "parent_tag_id", "level"),
        Index("ix_tags_usage_count", "usage_count"),
    )
```

**Indexes**:
- `name`: Fast lookup, uniqueness
- `parent_tag_id + level`: Efficient hierarchy queries
- `usage_count`: Sorting by popularity
- `deleted_at`: Soft delete filtering

#### 3.2 TagAssociationModel

```python
class TagAssociationModel(Base):
    __tablename__ = "tag_associations"

    id = Column(UUID, primary_key=True, default=uuid4)

    # Foreign key to Tag
    tag_id = Column(UUID, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)

    # Entity reference (RULE-019: denormalized)
    entity_type = Column(Enum(EntityType), nullable=False)  # BOOKSHELF | BOOK | BLOCK
    entity_id = Column(UUID, nullable=False, index=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    tag = relationship("TagModel", back_populates="tag_associations")

    # Constraints
    __table_args__ = (
        UniqueConstraint("tag_id", "entity_type", "entity_id", name="uq_tag_associations_tag_entity"),
        Index("ix_tag_associations_entity", "entity_type", "entity_id"),
    )
```

**Key Design**:
- Denormalized entity reference (not separate tables for Book/Bookshelf/Block)
- UNIQUE(tag_id, entity_type, entity_id) prevents duplicate associations
- INDEX(entity_type, entity_id) enables fast reverse lookup

---

### 4. Repository Layer (Query Patterns)

**Location**: `backend/api/app/modules/tag/repository.py`

#### 4.1 Abstract Interface

```python
class TagRepository(ABC):
    # CRUD
    async def save(self, tag: Tag) -> Tag
    async def get_by_id(self, tag_id: UUID) -> Optional[Tag]
    async def delete(self, tag_id: UUID) -> None  # Soft delete
    async def restore(self, tag_id: UUID) -> None

    # Hierarchy queries
    async def get_all_toplevel(limit=100) -> List[Tag]
    async def get_by_parent(parent_tag_id: UUID) -> List[Tag]

    # Search
    async def find_by_name(keyword: str, limit=20) -> List[Tag]
    async def find_most_used(limit=30) -> List[Tag]

    # Association queries
    async def find_by_entity(entity_type, entity_id) -> List[Tag]
    async def find_entities_with_tag(tag_id, entity_type) -> List[UUID]
    async def associate_tag_with_entity(tag_id, entity_type, entity_id) -> TagAssociation
    async def disassociate_tag_from_entity(tag_id, entity_type, entity_id) -> None

    # Validation
    async def check_name_exists(name, exclude_id=None) -> bool
    async def count_associations(tag_id) -> int
```

#### 4.2 Query Patterns (Soft Delete Enforcement)

```python
# All queries auto-filter deleted_at IS NULL

# Get top-level tags (for menu bar)
WHERE parent_tag_id IS NULL AND deleted_at IS NULL AND level = 0
ORDER BY usage_count DESC
LIMIT 30

# Search by name
WHERE LOWER(name) LIKE LOWER(?) AND deleted_at IS NULL
ORDER BY usage_count DESC

# Get tags for entity
SELECT tag_id FROM tag_associations
WHERE entity_type = ? AND entity_id = ?
THEN SELECT * FROM tags WHERE id IN (...) AND deleted_at IS NULL

# Reverse lookup: get all Books with tag X
SELECT entity_id FROM tag_associations
WHERE tag_id = ? AND entity_type = 'BOOK'
```

#### 4.3 Soft Delete Filtering

**All repository methods automatically filter out deleted_at IS NOT NULL**, ensuring:
- Deleted tags don't appear in menu bars
- Search results exclude deleted tags
- get_by_id still works (to support restore/delete flows)
- Associations are preserved (audit trail)

---

### 5. Service Layer (Business Logic)

**Location**: `backend/api/app/modules/tag/service.py`

#### 5.1 Tag Creation (RULE-018)

```python
async def create_tag(
    name: str,
    color: str,
    icon: Optional[str] = None,
    description: Optional[str] = None
) -> Tag:
    """
    Create top-level tag with full validation

    Validations:
    - name: non-empty, 1-50 chars, unique (case-insensitive)
    - color: hex format #RRGGBB or #RRGGBBAA
    - No duplicate active tags

    Raises: TagInvalidNameError, TagInvalidColorError, TagAlreadyExistsError
    """
    # L1: Input validation
    if not name or len(name) > 50:
        raise TagInvalidNameError("...")

    # L2: Business logic
    if await repository.check_name_exists(name):
        raise TagAlreadyExistsError(name)

    # L3: Domain creation
    tag = Tag.create_toplevel(name, color, icon, description)

    # L4: Persistence
    return await repository.save(tag)
```

#### 5.2 Tag Hierarchy (RULE-020)

```python
async def create_subtag(
    parent_tag_id: UUID,
    name: str,
    color: str,
    icon: Optional[str] = None
) -> Tag:
    """
    Create hierarchical sub-tag with cycle & depth checks

    Validations:
    - parent_tag_id must exist
    - parent must not be deleted
    - parent.level < 2 (max 3 levels total)
    - No cycles
    - name unique

    Raises: TagNotFoundError, TagInvalidHierarchyError, TagInvalidNameError
    """
    # L1: Validate parent exists
    parent = await repository.get_by_id(parent_tag_id)
    if not parent:
        raise TagNotFoundError(parent_tag_id)

    # L2: Depth check
    if parent.level >= 2:
        raise TagInvalidHierarchyError("Maximum hierarchy depth is 3")

    # L3: Name uniqueness
    if await repository.check_name_exists(name):
        raise TagAlreadyExistsError(name)

    # L4: Domain creation
    tag = Tag.create_subtag(parent_tag_id, name, color, icon, parent.level)

    # L5: Persistence
    return await repository.save(tag)
```

#### 5.3 Association Management (RULE-019)

```python
async def associate_tag_with_entity(
    tag_id: UUID,
    entity_type: EntityType,
    entity_id: UUID
) -> None:
    """
    Associate tag with entity (completely independent per entity_type)

    Effect:
    - Creates TagAssociation
    - Increments tag.usage_count
    - Idempotent: associating twice is safe

    Raises: TagNotFoundError, TagAlreadyDeletedError
    """
    # L1: Validate tag exists
    tag = await repository.get_by_id(tag_id)
    if not tag:
        raise TagNotFoundError(tag_id)

    if tag.is_deleted():
        raise TagOperationError("Cannot associate deleted tag")

    # L2: Create association (repository handles deduplication)
    assoc = await repository.associate_tag_with_entity(tag_id, entity_type, entity_id)

    # L3: Update usage count
    tag.increment_usage()
    await repository.save(tag)
```

#### 5.4 Query Methods

```python
async def get_tags_for_entity(entity_type, entity_id) -> List[Tag]
async def search_tags(keyword: str, limit: int = 20) -> List[Tag]
async def get_most_used_tags(limit: int = 30) -> List[Tag]  # Menu bar
async def get_tag_hierarchy(parent_tag_id=None) -> List[Tag]
```

---

### 6. Pydantic Schemas

**Location**: `backend/api/app/modules/tag/schemas.py`

#### 6.1 Request Models

```python
class CreateTagRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
    icon: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

class CreateSubtagRequest(BaseModel):
    parent_tag_id: UUID
    name: str = Field(..., min_length=1, max_length=50)
    color: str
    icon: Optional[str] = None

class UpdateTagRequest(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None

class AssociateTagRequest(BaseModel):
    entity_type: EntityTypeEnum  # BOOKSHELF | BOOK | BLOCK
    entity_id: UUID
```

#### 6.2 Response Models

```python
class TagResponse(BaseModel):
    id: UUID
    name: str
    color: str
    icon: Optional[str]
    level: int
    usage_count: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

class TagHierarchyResponse(BaseModel):
    id: UUID
    name: str
    children: List["TagHierarchyResponse"]

class EntityTagsResponse(BaseModel):
    entity_type: EntityTypeEnum
    entity_id: UUID
    tags: List[TagResponse]
    count: int

class TagListResponse(BaseModel):
    items: List[TagResponse]
    total: int
    page: int
    size: int
    has_more: bool
```

---

### 7. FastAPI Router (12 Endpoints)

**Location**: `backend/api/app/modules/tag/router.py`

#### 7.1 CRUD Operations

```
POST   /tags                    - Create top-level tag
POST   /tags/{id}/subtags       - Create sub-tag
GET    /tags/{id}               - Get tag details
PATCH  /tags/{id}               - Update tag (name/color/icon/description)
DELETE /tags/{id}               - Soft delete tag
POST   /tags/{id}/restore       - Restore soft-deleted tag
```

#### 7.2 Query Operations

```
GET    /tags                    - List tags (search/pagination/sort)
GET    /tags/hierarchy          - Get tag tree structure
GET    /tags/{entity_type}/{entity_id}/tags - Get tags on entity
```

#### 7.3 Association Operations

```
POST   /tags/{id}/associate     - Link tag to entity
DELETE /tags/{id}/associate     - Unlink tag from entity
```

#### 7.4 Dependency Injection Chain

```python
@router.post("/tags")
async def create_tag(
    request: CreateTagRequest,
    service: TagService = Depends(get_tag_service)
):
    """DI Chain: FastAPI → Service → Repository → Domain"""
    try:
        tag = await service.create_tag(...)
        return TagResponse.from_orm(tag)
    except TagAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=e.to_dict())
```

#### 7.5 Exception Mapping

```python
TagNotFoundError → 404
TagAlreadyExistsError → 409
TagInvalidNameError → 422
TagInvalidColorError → 422
TagInvalidHierarchyError → 422
TagAlreadyDeletedError → 409
TagOperationError → 500
```

---

## Integration Points with Other Modules

### With Bookshelf/Book/Block Modules

1. **Deletion Cascade**
   - When Book is deleted: remove TagAssociation records (CASCADE)
   - When Bookshelf is deleted: remove TagAssociation records (CASCADE)
   - Tag itself is NOT deleted (soft delete pattern)

2. **UI Queries**
   - Get Book details → call `/tags/book/{id}/tags` to fetch tags
   - Get Bookshelf → call `/tags/bookshelf/{id}/tags` separately
   - Menu bar → call `/tags?sort_by=usage_count` for top 30 tags

3. **Bulk Tagging**
   - Create Book + auto-tag: call POST /books, then POST /tags/{id}/associate multiple times
   - Batch move books: move books, then update tags separately

---

## Testing Strategy

### Test Files

```
backend/api/app/tests/test_tag/
├── test_domain.py              # Domain invariants (18 tests)
│   ├── Value object validation
│   ├── Factory methods
│   ├── Soft delete lifecycle
│   ├── Usage count updates
│   └── Domain events
│
├── test_repository.py          # Persistence (14 tests)
│   ├── CRUD operations
│   ├── Hierarchy queries
│   ├── Search patterns
│   ├── Association management
│   ├── Soft delete filtering
│   └── Uniqueness constraints
│
├── test_service.py             # Business logic (planned)
│   ├── Creation with validation
│   ├── Hierarchy depth checks
│   ├── Cycle detection
│   ├── Association idempotency
│   └── Usage count caching
│
└── test_router.py              # API endpoints (planned)
    ├── CRUD endpoints
    ├── Exception mapping
    ├── Pagination
    └── DI chain validation
```

### Key Test Cases

- [ ] Create top-level tag (valid/invalid name/color)
- [ ] Create subtag with depth limit
- [ ] Unique name enforcement
- [ ] Soft delete → hide from queries
- [ ] Restore deleted tag
- [ ] Associate tag with multiple entity types (independent)
- [ ] Disassociate idempotency
- [ ] Usage count auto-update
- [ ] Hierarchy queries (parent + children)
- [ ] Search pagination
- [ ] Exception HTTP mapping (404/409/422/500)

---

## Configuration & Deployment

### Environment Variables

```bash
TAG_SEARCH_LIMIT_DEFAULT=20
TAG_HIERARCHY_DEPTH_MAX=3
TAG_USAGE_COUNT_CACHE_TTL=3600  # 1 hour (for future invalidation)
```

### Database Migrations

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    color VARCHAR(9) NOT NULL,
    icon VARCHAR(50),
    description TEXT,
    parent_tag_id UUID REFERENCES tags(id) ON DELETE SET NULL,
    level INT NOT NULL DEFAULT 0,
    usage_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    deleted_at TIMESTAMP,
    INDEX ix_tags_name (name),
    INDEX ix_tags_parent_level (parent_tag_id, level),
    INDEX ix_tags_usage_count (usage_count),
    INDEX ix_tags_deleted_at (deleted_at)
);

CREATE TABLE tag_associations (
    id UUID PRIMARY KEY,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    entity_type ENUM('BOOKSHELF', 'BOOK', 'BLOCK') NOT NULL,
    entity_id UUID NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (tag_id, entity_type, entity_id),
    INDEX ix_tag_assoc_entity (entity_type, entity_id),
    INDEX ix_tag_assoc_tag (tag_id)
);
```

---

## Decisions & Trade-offs

| Decision | Rationale | Alternative Rejected |
|----------|-----------|---------------------|
| **Denormalized entity_type + entity_id** | Single table supports all entity types; fast reverse lookup | Separate tables per entity type (complex queries, JOINs) |
| **Hierarchical parent_tag_id** | Supports multi-level categorization; efficient tree queries | Flat tag list only (limits future scalability) |
| **Soft delete with preserved associations** | Enables restore; audit trail; GDPR compliance | Hard delete (loses history) |
| **usage_count cache** | O(1) menu bar queries (popular tags) | Calculate on-the-fly (expensive JOIN + COUNT) |
| **Entity_type as ENUM** | Type safety; prevents invalid types | String (allows typos) |
| **Denormalized associations** | One table simpler than polymorphic patterns | SQLAlchemy joined table inheritance (complex) |

---

## Future Enhancements

### Phase 2.5 (Planned)

1. **Elasticsearch Integration**
   - Sync Tag names to ES for full-text search
   - Support fuzzy matching + typo tolerance
   - Pinyin search support (for Chinese tags)

2. **Tag Suggestions**
   - ML-based tag recommendations when creating Book
   - Auto-tag based on content (future AI integration)

3. **Tag Analytics**
   - Dashboard: most used tags by time period
   - Tag usage trends
   - Export tag hierarchy

4. **Tag Permissions**
   - User-created tags vs. system tags
   - Shared tags across Library users

### Phase 3 (Post-MVP)

1. **Tag Templates**
   - Predefined tag sets for common workflows
   - User-saved templates

2. **Auto-Tagging Pipeline**
   - Batch tag application based on patterns
   - Trigger-based auto-tagging (when Book created with keyword)

---

## References

- ADR-020: Bookshelf Router/Schemas/Exceptions
- ADR-021: Book Router/Schemas/Exceptions
- ADR-022: Block Router/Schemas/Exceptions
- DDD_RULES.yaml: RULE-018, RULE-019, RULE-020, POLICY-009, POLICY-010

---

**Approval Status**: ✅ ACCEPTED
**Reviewed By**: Architecture Team
**Date Accepted**: November 13, 2025
