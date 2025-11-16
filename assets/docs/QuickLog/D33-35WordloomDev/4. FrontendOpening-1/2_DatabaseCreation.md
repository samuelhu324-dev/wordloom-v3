老数据库 vs 新数据库：对比框架
让我给你一个逐表对比方案：

# 数据库迁移对比表

## 表 1: Libraries (新增/改名)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 表名 | `bookshelves` (复数) | `libraries` (单数) | ✅ 概念升级 | RULE-001 |
| 主键 | `id (UUID)` | `id (UUID)` | ✅ 同 | - |
| 用户关联 | `user_id` | `user_id` | ✅ 同 | RULE-002 |
| 名称 | `name VARCHAR(255)` | `name VARCHAR(255)` | ✅ 同 | RULE-003 |
| 描述 | `description TEXT` | `description TEXT` | ✅ 同 | - |
| 时间戳 | `created_at, updated_at` | `created_at, updated_at` | ✅ 同 | - |
| **约束** | `UNIQUE(user_id)` | `UNIQUE(user_id)` | ✅ 同 | RULE-001 |
| **新增** | - | `soft_deleted_at` (Basement) | ✨ 新概念 | BASEMENT-001 |

✅ **迁移策略:**
- 老 bookshelves → 新 libraries (1:1 映射)
- 保留所有字段值
- 新增 soft_deleted_at = NULL (初始)

---

## 表 2: Bookshelves (改名 + 升级)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 表名 | `bookshelves` | `bookshelves` | ✅ 同 | - |
| 主键 | `id (UUID)` | `id (UUID)` | ✅ 同 | - |
| Library 关联 | `parent_id (FK)` | `library_id (FK)` | 🔄 改名 | RULE-005 |
| 名称 | `name VARCHAR(255)` | `name VARCHAR(255)` | ✅ 同 | RULE-006 |
| 约束 | `UNIQUE(parent_id, name)` | `UNIQUE(library_id, name)` | ✅ 同 | RULE-006 |
| **新增** | - | `is_basement BOOLEAN` | ✨ 新字段 | RULE-010 |
| **新增** | - | `color VARCHAR(7)` | ✨ UI 功能 | - |
| **新增** | - | `position INT` | ✨ 排序 | - |
| **新增** | - | `status ENUM(ACTIVE/ARCHIVED/DELETED)` | ✨ 状态机 | RULE-010 |

🔄 **迁移策略:**
- 老 bookshelves → 新 bookshelves
- `parent_id` → `library_id` (同值)
- `is_basement = FALSE` for all old records
- `status = 'ACTIVE'` for all old records
- 自动创建一个 Basement bookshelf: `INSERT INTO bookshelves (name, library_id, is_basement, status) VALUES ('Basement', {lib_id}, TRUE, 'ACTIVE')`

---

## 表 3: Books / OrbitNotes (改名 + 大升级)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 表名 | `orbit_notes` | `books` | 🔄 改名 | - |
| 主键 | `id (UUID)` | `id (UUID)` | ✅ 同 | - |
| 标题 | `title TEXT` | `title VARCHAR(255)` | 🔄 类型变更 | RULE-009 |
| Bookshelf 关联 | `bookshelf_id (FK)` | `bookshelf_id (FK)` | ✅ 同 | RULE-010 |
| **新增** | - | `library_id (FK)` | ✨ 冗余FK (性能) | RULE-009 |
| **新增** | - | `author VARCHAR(255)` | ✨ 元数据 | - |
| 描述 | `summary TEXT` | `summary TEXT` | ✅ 同 | - |
| **新增** | - | `priority INT` | ✨ 优先级 | - |
| **新增** | - | `urgency INT` | ✨ 紧急度 | - |
| **新增** | - | `due_date DATETIME` | ✨ 截止日期 | - |
| **新增** | - | `soft_deleted_at` | ✨ Basement | RULE-012 |
| 时间戳 | `created_at, updated_at` | `created_at, updated_at` | ✅ 同 | - |

⚠️ **迁移策略:**
- 老 orbit_notes → 新 books (需 mapping)
- 从 bookshelf 查询 library_id，填入新 FK
- soft_deleted_at = NULL for all old records
- 若老表有已删记录，需识别并设置 soft_deleted_at

---

## 表 4: Blocks / blocks_json (大重构)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 存储方式 | JSON数组 (books_json内嵌) | 独立表 `blocks` | 🔄 数据库设计升级 | - |
| 表名 | `books.blocks_json` (JSONB) | `blocks` (独立表) | ✨ 规范化 | - |
| 主键 | - | `id (UUID)` | ✨ 新增 | - |
| Book 关联 | implicit (parent) | `book_id (FK)` | ✨ 显式FK | RULE-016 |
| 内容 | 嵌入JSON | `content TEXT` | 🔄 分离 | RULE-014 |
| 类型 | `type` (text/code/image 等) | `block_type ENUM` | 🔄 约束化 | RULE-014 |
| **新增** | - | `order DECIMAL(19,10)` | ✨ Fractional Index | RULE-015 |
| **新增** | - | `soft_deleted_at` | ✨ Paperballs | POLICY-008 |
| **新增** | - | `deleted_prev_id, deleted_next_id, deleted_section_path` | ✨ Paperballs恢复 | PAPERBALLS-POS-001/002/003 |

❌ **迁移很复杂:**
- 需解析 books.blocks_json JSONB数组
- 为每个block插入新行到 blocks表
- 计算 order (Fractional Index) - 不能简单用sequence
- 软删除信息可能丢失 (需历史追溯)

---

## 表 5: Tags (新增)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 表名 | `tags` (可能有) | `tags` | ✅ 可能同 | - |
| 主键 | `id (UUID)` | `id (UUID)` | ✅ 同 | - |
| **新增** | - | `user_id (FK)` | ✨ 多租户 | - |
| 名称 | `name VARCHAR` | `name VARCHAR(50)` | 🔄 约束 | RULE-018 |
| **新增** | - | `parent_tag_id (FK)` | ✨ 层级 | RULE-020 |
| **新增** | - | `color VARCHAR(7)` | ✨ UI | - |
| **新增** | - | `usage_count INT` | ✨ 缓存 | POLICY-010 |
| 约束 | - | `UNIQUE(user_id, name)` | ✨ 多租户隔离 | - |

✅ **迁移策略:**
- 老tags→新tags (如果架构兼容)
- 新增 user_id (从library推导)
- parent_tag_id = NULL for all

---

## 表 6: Media (新增)

| 方面 | 老 WordLoom | 新 Wordloom v3 | 差异 | 规则 |
|------|-----------|---------------|------|------|
| 表名 | `media` (可能有) | `media` | ✅ 可能同 | - |
| **新增** | - | 完整结构 | ✨ 全新设计 | - |
| 字段 | - | id, filename, storage_key, mime_type, file_size, width, height, duration_ms, state, trash_at, deleted_at | ✨ 完整元数据 | POLICY-010 |
| 约束 | - | UNIQUE(storage_key), state filtering, 30-day retention | ✨ Vault模式 | - |

---

## 对比总结

| 表 | 老数据 | 新设计 | 冲突? | 参考价值 |
|----|-------|-------|--------|---------|
| **libraries** | - | ✅ 新 | ❌ 无 | ✅ 创建概念 |
| **bookshelves** | ✅ 有 | ✅ 扩展 | ⚠️ 小 | ✅✅ 字段映射 |
| **books** | ✅ 有 (orbit_notes) | ✅ 改名 | ⚠️ 中等 | ✅ 大部分同 |
| **blocks** | ✅ 有 (JSON嵌入) | ✅ 新表 | ⚠️ 大 | ⚠️ 需特殊处理 |
| **tags** | ✅ 可能有 | ✅ 升级 | ⚠️ 中等 | ✅ 有参考 |
| **media** | ✅ 可能有 | ✅ 新设计 | ⚠️ 中等 | ⚠️ 需特殊处理 |

✅ 有参考价值的字段：

libraries: 全部可用
bookshelves: 95% 可用（只需加 is_basement, status, color）
books/orbit_notes: 80% 可用（改名 + 新增FK + 元数据）
tags: 70% 可用（需新增 user_id, parent_id, color）
⚠️ 难迁移的：

blocks/blocks_json: 需拆解JSON + 计算 Fractional Index
软删除字段: 老数据可能没有历史记录

分阶段建表方案（对标三份 RULES）
我建议按照 DDD_RULES 的聚合根层级 来建表，同时 参考老数据库，但 严格按新规则验证。

Phase A: Week 1 - 核心表创建（不导数据）
目标：验证后端 API 能工作 + 新规则能执行

-- ✅ Day 1-2: 建这 6 张表（干净，无老数据）

-- 1. libraries (新增)
CREATE TABLE libraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id),
    CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 2. bookshelves (改名 + 升级)
CREATE TABLE bookshelves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES libraries(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',
    position INT DEFAULT 0,
    is_basement BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE|ARCHIVED|DELETED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(library_id, name),
    INDEX(is_basement),
    INDEX(status)
);

-- 3. books (改名 + 升级)
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES libraries(id),
    bookshelf_id UUID NOT NULL REFERENCES bookshelves(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    summary TEXT,
    priority INT DEFAULT 0,
    urgency INT DEFAULT 0,
    due_date TIMESTAMP DEFAULT NULL,
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(bookshelf_id),
    INDEX(library_id),
    INDEX(soft_deleted_at)
);

-- 4. blocks (新增)
CREATE TABLE blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    block_type VARCHAR(50) DEFAULT 'text', -- text|heading|code|image|quote|list|table|divider
    sort_key DECIMAL(20,10) DEFAULT 0, -- Fractional Index
    deleted_prev_id UUID DEFAULT NULL,
    deleted_next_id UUID DEFAULT NULL,
    deleted_section_path VARCHAR(500) DEFAULT NULL,
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(book_id),
    INDEX(sort_key),
    INDEX(soft_deleted_at)
);

-- 5. tags (新增)
CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    name VARCHAR(50) NOT NULL,
    parent_tag_id UUID DEFAULT NULL REFERENCES tags(id) ON DELETE SET NULL,
    color VARCHAR(7) DEFAULT '#6366F1',
    usage_count INT DEFAULT 0,
    soft_deleted_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name),
    INDEX(user_id),
    INDEX(parent_tag_id)
);

-- 6. media (新增)
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) UNIQUE NOT NULL,
    mime_type VARCHAR(100),
    file_size INT,
    width INT DEFAULT NULL,
    height INT DEFAULT NULL,
    duration_ms INT DEFAULT NULL,
    state VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE|TRASH
    trash_at TIMESTAMP DEFAULT NULL,
    deleted_at TIMESTAMP DEFAULT NULL,
    purge_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(user_id),
    INDEX(state),
    INDEX(trash_at)
);

-- 关联表
CREATE TABLE block_tags (
    block_id UUID NOT NULL REFERENCES blocks(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(block_id, tag_id)
);

CREATE TABLE book_tags (
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY(book_id, tag_id)
);

CREATE TABLE media_associations (
    media_id UUID NOT NULL REFERENCES media(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL, -- bookshelf|book|block|tag
    entity_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_id, entity_type, entity_id)
);

-- 搜索索引表
CREATE TABLE search_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- block|book|bookshelf|tag
    entity_id UUID NOT NULL,
    content_text TEXT,
    search_vector tsvector,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX(entity_type),
    INDEX(updated_at),
    GIN INDEX(search_vector)
);

数据库命名方案（推荐）
生产环境结构
├── wordloom (主库 - 当前)
├── wordloom_dev (开发库)
├── wordloom_staging (测试库)
└── wordloom_backup (备份库)

Connection String:
- 本地开发: postgresql://postgres:pgpass@127.0.0.1:5433/wordloom
- 环境变量: DATABASE_URL=postgresql://postgres:pgpass@127.0.0.1:5433/wordloom


