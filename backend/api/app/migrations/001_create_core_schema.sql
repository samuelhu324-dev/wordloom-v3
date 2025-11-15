-- ============================================
-- Wordloom v3 Core Database Schema
-- ============================================
-- 完整数据库表结构，基于 DDD_RULES.yaml + HEXAGONAL_RULES.yaml + VISUAL_RULES.yaml
-- 最后更新：2025-11-15
-- 版本：1.0
-- 对应 ADR-053-wordloom-core-database-schema.md

-- ============================================
-- Extensions
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================
-- DOMAIN 1: Libraries (聚合根)
-- RULES: RULE-001, RULE-002, RULE-003, BASEMENT-001
-- ============================================

CREATE TABLE libraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),

    -- Soft delete (Basement concept)
    soft_deleted_at TIMESTAMP DEFAULT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(user_id),
    CONSTRAINT check_name_length CHECK (LENGTH(name) > 0)
);

CREATE INDEX idx_libraries_user_id ON libraries(user_id);
CREATE INDEX idx_libraries_soft_deleted_at ON libraries(soft_deleted_at);

COMMENT ON TABLE libraries IS 'RULE-001: User can have exactly 1 library. DDD AggregateRoot.';
COMMENT ON COLUMN libraries.soft_deleted_at IS 'BASEMENT-001: Soft deletion timestamp (NULL = not deleted)';

-- ============================================
-- DOMAIN 2: Bookshelves (子聚合 / 数据容器)
-- RULES: RULE-004, RULE-005, RULE-006, RULE-010
-- ============================================

CREATE TABLE bookshelves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,

    name VARCHAR(255) NOT NULL,
    description TEXT,
    color VARCHAR(7) DEFAULT '#3B82F6',
    position INT DEFAULT 0,

    -- Special bookshelves
    is_basement BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'ACTIVE',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(library_id, name),
    CONSTRAINT check_name_length CHECK (LENGTH(name) > 0),
    CONSTRAINT check_color_format CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

CREATE INDEX idx_bookshelves_library_id ON bookshelves(library_id);
CREATE INDEX idx_bookshelves_is_basement ON bookshelves(is_basement);
CREATE INDEX idx_bookshelves_status ON bookshelves(status);

COMMENT ON TABLE bookshelves IS 'RULE-004: Max 100 bookshelves per library. RULE-006: Name unique per library.';
COMMENT ON COLUMN bookshelves.is_basement IS 'RULE-010: Special bookshelf for soft-deleted books';

-- ============================================
-- DOMAIN 3: Books (独立聚合根)
-- RULES: RULE-009, RULE-010, RULE-011, RULE-012, BASEMENT-002
-- ============================================

CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    bookshelf_id UUID NOT NULL REFERENCES bookshelves(id) ON DELETE CASCADE,

    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    summary TEXT,
    isbn VARCHAR(20),

    -- Metadata
    priority INT DEFAULT 0,
    urgency INT DEFAULT 0,
    due_date TIMESTAMP,
    pages_total INT,
    reading_progress INT DEFAULT 0,

    -- Status tracking
    status VARCHAR(50) DEFAULT 'ACTIVE',
    last_read_at TIMESTAMP,

    -- Soft delete (Basement)
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    deleted_from_shelf_id UUID REFERENCES bookshelves(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_title_length CHECK (LENGTH(title) > 0),
    CONSTRAINT check_priority CHECK (priority BETWEEN 0 AND 5),
    CONSTRAINT check_progress CHECK (reading_progress BETWEEN 0 AND 100)
);

CREATE INDEX idx_books_bookshelf_id ON books(bookshelf_id);
CREATE INDEX idx_books_library_id ON books(library_id);
CREATE INDEX idx_books_soft_deleted_at ON books(soft_deleted_at);
CREATE INDEX idx_books_status ON books(status);

COMMENT ON TABLE books IS 'RULE-009: Book is independent AR. RULE-012: Soft delete moves to Basement.';
COMMENT ON COLUMN books.soft_deleted_at IS 'BASEMENT-002: Soft delete timestamp (NULL = active)';

-- ============================================
-- DOMAIN 4: Blocks (最小单位 / 值对象集合)
-- RULES: RULE-013, RULE-014, RULE-015, RULE-016, PAPERBALLS-POS-001/002/003
-- ============================================

CREATE TABLE blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,

    content TEXT NOT NULL,
    block_type VARCHAR(50) NOT NULL DEFAULT 'text',

    -- Fractional Index for infinite ordering (RULE-015)
    sort_key NUMERIC(20, 10) NOT NULL DEFAULT 0,

    -- Properties
    language VARCHAR(50),
    collapsed BOOLEAN DEFAULT FALSE,

    -- Soft delete (Paperballs recovery)
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    deleted_prev_block_id UUID REFERENCES blocks(id) ON DELETE SET NULL,
    deleted_next_block_id UUID REFERENCES blocks(id) ON DELETE SET NULL,
    deleted_section_path VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT check_content_not_empty CHECK (LENGTH(TRIM(content)) > 0),
    CONSTRAINT valid_block_type CHECK (block_type IN (
        'text', 'heading', 'code', 'image', 'quote', 'list', 'table',
        'divider', 'latex', 'mermaid', 'custom'
    ))
);

CREATE INDEX idx_blocks_book_id ON blocks(book_id);
CREATE INDEX idx_blocks_sort_key ON blocks(book_id, sort_key);
CREATE INDEX idx_blocks_soft_deleted_at ON blocks(soft_deleted_at);

COMMENT ON TABLE blocks IS 'RULE-015: Fractional Index for infinite drag/drop reordering.';
COMMENT ON COLUMN blocks.sort_key IS 'RULE-015: Decimal(20,10) for fractional positioning';
COMMENT ON COLUMN blocks.soft_deleted_at IS 'PAPERBALLS-POS-001: Recovery metadata';

-- ============================================
-- DOMAIN 5: Tags (全局价值对象)
-- RULES: RULE-018, RULE-019, RULE-020, POLICY-010
-- ============================================

CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,

    name VARCHAR(50) NOT NULL,
    description TEXT,
    parent_tag_id UUID REFERENCES tags(id) ON DELETE SET NULL,
    color VARCHAR(7) DEFAULT '#6366F1',
    icon_emoji VARCHAR(10),

    -- Metadata
    usage_count INT DEFAULT 0,

    -- Soft delete
    soft_deleted_at TIMESTAMP DEFAULT NULL,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    UNIQUE(user_id, name),
    CONSTRAINT check_name_length CHECK (LENGTH(name) > 0),
    CONSTRAINT check_color_format CHECK (color ~ '^#[0-9A-Fa-f]{6}$')
);

CREATE INDEX idx_tags_user_id ON tags(user_id);
CREATE INDEX idx_tags_parent_tag_id ON tags(parent_tag_id);
CREATE INDEX idx_tags_soft_deleted_at ON tags(soft_deleted_at);

COMMENT ON TABLE tags IS 'RULE-018: Global cross-entity tags. RULE-020: Hierarchical structure.';

-- ============================================
-- DOMAIN 6: Media (全局资产库)
-- RULES: POLICY-009, POLICY-010, VAULT-001
-- ============================================

CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,

    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) UNIQUE NOT NULL,
    mime_type VARCHAR(100),
    file_size INT NOT NULL,

    -- Image metadata
    width INT,
    height INT,

    -- Video metadata
    duration_ms INT,

    -- State management
    state VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    trash_at TIMESTAMP,
    purge_at TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_state CHECK (state IN ('ACTIVE', 'TRASH')),
    CONSTRAINT check_file_size CHECK (file_size > 0)
);

CREATE INDEX idx_media_user_id ON media(user_id);
CREATE INDEX idx_media_state ON media(state);
CREATE INDEX idx_media_trash_at ON media(trash_at);
CREATE INDEX idx_media_storage_key ON media(storage_key);

COMMENT ON TABLE media IS 'VAULT-001: 30-day trash retention before purge. POLICY-010: Global asset management.';

-- ============================================
-- DOMAIN 7: Chronicle (时间追踪 - 新增)
-- RULES: CHRONICLE-001, CHRONICLE-002
-- ============================================

CREATE TABLE chronicle_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,

    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    action VARCHAR(50) NOT NULL,

    data_snapshot JSONB,
    change_details JSONB,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chronicle_user_id ON chronicle_events(user_id);
CREATE INDEX idx_chronicle_entity ON chronicle_events(entity_type, entity_id);
CREATE INDEX idx_chronicle_created_at ON chronicle_events(created_at);

COMMENT ON TABLE chronicle_events IS 'CHRONICLE-001: Full audit trail of all changes.';

-- ============================================
-- ASSOCIATION TABLES: Many-to-Many Relationships
-- ============================================

CREATE TABLE block_tags (
    block_id UUID NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(block_id, tag_id)
);

CREATE INDEX idx_block_tags_tag_id ON block_tags(tag_id);

COMMENT ON TABLE block_tags IS 'RULE-021: Blocks can have multiple tags. Cascade on delete.';

CREATE TABLE book_tags (
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(book_id, tag_id)
);

CREATE INDEX idx_book_tags_tag_id ON book_tags(tag_id);

CREATE TABLE media_associations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    media_id UUID NOT NULL REFERENCES media(id) ON DELETE CASCADE,

    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,

    position INT DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(media_id, entity_type, entity_id)
);

CREATE INDEX idx_media_associations_entity ON media_associations(entity_type, entity_id);

-- ============================================
-- SEARCH INDEX TABLE (denormalized for FTS)
-- RULES: SEARCH-001, SEARCH-002
-- ============================================

CREATE TABLE search_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,

    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,

    title VARCHAR(255),
    content_text TEXT,
    search_vector tsvector,

    last_indexed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(entity_type, entity_id)
);

CREATE INDEX idx_search_index_user_id ON search_index(user_id);
CREATE INDEX idx_search_index_vector ON search_index USING gin(search_vector);

COMMENT ON TABLE search_index IS 'SEARCH-001: Denormalized search index for full-text search.';

-- ============================================
-- TRIGGER: Auto-update timestamps
-- ============================================

CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_libraries_timestamp BEFORE UPDATE ON libraries
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_bookshelves_timestamp BEFORE UPDATE ON bookshelves
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_books_timestamp BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_blocks_timestamp BEFORE UPDATE ON blocks
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_tags_timestamp BEFORE UPDATE ON tags
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_media_timestamp BEFORE UPDATE ON media
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ============================================
-- TRIGGER: Auto-create Basement on Library creation
-- ============================================

CREATE OR REPLACE FUNCTION create_library_basement()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO bookshelves (library_id, name, is_basement, status)
    VALUES (NEW.id, 'Basement', TRUE, 'ACTIVE');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER create_basement_trigger AFTER INSERT ON libraries
    FOR EACH ROW EXECUTE FUNCTION create_library_basement();

-- ============================================
-- VIEWS (for common queries)
-- ============================================

CREATE VIEW active_books AS
SELECT * FROM books
WHERE soft_deleted_at IS NULL;

CREATE VIEW active_blocks AS
SELECT * FROM blocks
WHERE soft_deleted_at IS NULL;

CREATE VIEW basement_books AS
SELECT * FROM books
WHERE soft_deleted_at IS NOT NULL
ORDER BY soft_deleted_at DESC;

COMMENT ON VIEW basement_books IS 'BASEMENT-002: All soft-deleted books for recovery view.';

-- ============================================
-- SEED DATA (Demo - Optional)
-- ============================================

-- Uncomment to add demo data for testing
-- INSERT INTO libraries (id, user_id, name, description)
-- VALUES (
--     gen_random_uuid(),
--     1,
--     'My First Library',
--     'Demo library for testing Wordloom v3'
-- ) ON CONFLICT DO NOTHING;
