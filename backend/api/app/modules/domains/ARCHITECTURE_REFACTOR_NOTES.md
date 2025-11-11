# Wordloom v3 架构重构笔记（2025-11-12）

## 概述

基于深度分析，完成了三大架构决策的 Domain 层实现：

1. **独立聚合根模式** - 所有聚合（Library/Bookshelf/Book/Block）通过 FK 关联，而非嵌套
2. **Basement 模式** - 软删除 + 回收站，用户可恢复误删除
3. **真实转移** - Book 跨 Bookshelf 转移采用 Move Semantics（真转移），不是复制+删除

---

## 已完成的改动

### 1. Library Domain (`library/domain.py`)

```python
# ✅ 新增
- basement_bookshelf_id: UUID  # 自动创建的 Basement 书架
- BasementCreated 事件          # 创建 Library 时同时创建 Basement

# 改动
- create() 方法同时发出两个事件：
  - LibraryCreated(library_id, user_id, name)
  - BasementCreated(basement_id, library_id, user_id)
```

**关键设计：**
- Library.create() 自动生成 basement_bookshelf_id（UUID）
- 两个事件自动发出，Service 层需监听 BasementCreated 创建实际的 Bookshelf 数据
- basement_bookshelf_id 存储在 libraries 表中

---

### 2. Bookshelf Domain (`bookshelf/domain.py`)

```python
# ✅ 新增
class BookshelfType(Enum):
    NORMAL = "normal"
    BASEMENT = "basement"  # 特殊类型

# ✅ 新增字段
- type: BookshelfType           # NORMAL or BASEMENT
- is_hidden: bool               # Basement 隐藏

# ✅ 新增方法
- @property is_basement: bool
- mark_as_basement(): void      # 标记为 Basement（系统调用）

# ✅ 改动
- mark_deleted() 检查：Basement 不能被删除 ❌

# ❌ 移除（暂时保留，但不使用）
- BookshelfPinned / Unpinned 事件（合并到状态管理）
- BookshelfFavorited / Unfavorited 事件
```

**关键设计：**
- Bookshelf 通过 library_id FK 关联 Library（不包含 Library 对象）
- 独立聚合根：修改 Bookshelf 不需要锁 Library
- Basement 是特殊的 Bookshelf，隐藏且不能删除
- Pin/Favorite 逻辑移到 Service 层（暂不发出事件）

---

### 3. Book Domain (`book/domain.py`)

```python
# ✅ 新增字段
- library_id: UUID                      # 冗余 FK（权限检查）
- soft_deleted_at: Optional[datetime]   # Basement 标记

# ✅ 新增事件
- BookMovedToBookshelf(old_id, new_id, book_id)  # 跨架转移
- BookMovedToBasement(old_id, basement_id, deleted_at)  # 删除
- BookRestoredFromBasement(basement_id, restore_to_id, restored_at)  # 恢复

# ✅ 新增方法
- move_to_bookshelf(new_bookshelf_id): void
  └─ 真实转移：UPDATE bookshelf_id = new_id
  └─ 发出 BookMovedToBookshelf 事件

- move_to_basement(basement_id): void
  └─ 软删除：bookshelf_id = basement_id, soft_deleted_at = now
  └─ 发出 BookMovedToBasement 事件

- restore_from_basement(restore_to_id): void
  └─ 恢复：bookshelf_id = restore_to_id, soft_deleted_at = None
  └─ 发出 BookRestoredFromBasement 事件

- @property is_in_basement: bool

# ✅ 改动
- __init__ 新增 library_id 和 soft_deleted_at 参数
```

**关键设计：**
- 独立聚合根：Book 通过 bookshelf_id 和 library_id FK 关联
- Basement 标记通过 soft_deleted_at，而非数据库状态列
- 真实转移：move_to_bookshelf() 只是 UPDATE bookshelf_id（原子性）
- 删除 = 转移到 Basement（Book ID 不变，用户可恢复）

---

### 4. Block Domain (`block/domain.py`)

```python
# ✅ 确认状态
- 已是独立聚合根 ✅
- 包含 book_id, bookshelf_id, library_id FK ✅
- 支持标题层级（title_level 1-3）✅

# ⚠️ 待调整（非紧急）
- 事件体系（BlockContentChanged 等）已完整
- 暂无改动需要
```

**关键设计：**
- Block 编辑时不需要锁 Book（独立聚合）
- 冗余 FK（bookshelf_id, library_id）用于：
  - Bookshelf 删除时快速查询级联 Blocks
  - 权限检查时无需 JOIN
- Title 层级（1-3）支持标题导出

---

## Service 层改动预告（下步实现）

### LibraryService

```python
async def create_library(user_id, name) -> Library:
    library = Library.create(user_id, name)

    # 监听 BasementCreated 事件，创建实际 Bookshelf
    for event in library.events:
        if isinstance(event, BasementCreated):
            basement = Bookshelf.create_basement(
                bookshelf_id=event.basement_bookshelf_id,
                library_id=event.library_id
            )
            await bookshelf_repo.save(basement)

    await library_repo.save(library)
```

### BookshelfService

```python
async def delete_bookshelf(bookshelf_id, user_id) -> None:
    """删除 Bookshelf 时，将其 Books 转移到 Basement"""
    bookshelf = await bookshelf_repo.get_by_id(bookshelf_id)

    if bookshelf.is_basement:
        raise ValueError("Cannot delete Basement")

    # 查询所有 Books
    books = await book_repo.get_by_bookshelf_id(bookshelf_id)

    # 获取 Basement ID
    library = await library_repo.get_by_id(bookshelf.library_id)
    basement_id = library.basement_bookshelf_id

    # 转移每个 Book 到 Basement
    for book in books:
        book.move_to_basement(basement_id)
        await book_repo.save(book)

    # 删除 Bookshelf
    bookshelf.mark_deleted()
    await bookshelf_repo.save(bookshelf)
```

### BookService

```python
async def delete_book(book_id, user_id) -> None:
    """删除 Book（转移到 Basement）"""
    book = await book_repo.get_by_id(book_id)
    library = await library_repo.get_by_id(book.library_id)

    # 转移到 Basement
    book.move_to_basement(library.basement_bookshelf_id)
    await book_repo.save(book)

async def restore_book(book_id, restore_to_bookshelf_id, user_id) -> Book:
    """从 Basement 恢复 Book"""
    book = await book_repo.get_by_id(book_id)

    if not book.is_in_basement:
        raise ValueError("Book is not in Basement")

    book.restore_from_basement(restore_to_bookshelf_id)
    await book_repo.save(book)
    return book

async def move_book_to_bookshelf(book_id, target_shelf_id, user_id) -> Book:
    """转移 Book 到另一个 Bookshelf"""
    book = await book_repo.get_by_id(book_id)
    target_shelf = await bookshelf_repo.get_by_id(target_shelf_id)

    # 权限检查
    if book.library_id != target_shelf.library_id:
        raise PermissionError("Target shelf is in different library")

    if target_shelf.is_basement:
        raise ValueError("Cannot move book to Basement")

    # 真实转移
    book.move_to_bookshelf(target_shelf_id)
    await book_repo.save(book)
    return book

async def purge_basement(library_id, older_than_days=30) -> int:
    """清理 Basement 中超过 30 天的 Books"""
    library = await library_repo.get_by_id(library_id)
    basement_id = library.basement_bookshelf_id

    # 查询超期 Books
    old_date = datetime.utcnow() - timedelta(days=older_than_days)
    books = await book_repo.find_in_basement_before(basement_id, old_date)

    count = 0
    for book in books:
        # 硬删除（包括其 Blocks 和媒体）
        await book_repo.delete(book.id)
        count += 1

    return count
```

---

## 数据库迁移（暂不执行，仅供参考）

```sql
-- Libraries 表新增字段
ALTER TABLE libraries ADD COLUMN basement_bookshelf_id UUID;

-- Bookshelves 表新增字段
ALTER TABLE bookshelves ADD COLUMN type VARCHAR(50) DEFAULT 'normal';
ALTER TABLE bookshelves ADD COLUMN is_hidden BOOLEAN DEFAULT false;

-- Books 表新增字段
ALTER TABLE books ADD COLUMN library_id UUID;
ALTER TABLE books ADD COLUMN soft_deleted_at TIMESTAMP NULL;

-- Blocks 表新增字段（可选）
ALTER TABLE blocks ADD COLUMN bookshelf_id UUID;
ALTER TABLE blocks ADD COLUMN library_id UUID;

-- 创建 Basement Bookshelves
INSERT INTO bookshelves (id, library_id, name, type, is_hidden, created_at)
SELECT gen_random_uuid(), id, '🗑 Basement', 'basement', true, now()
FROM libraries;

-- 更新 libraries.basement_bookshelf_id
UPDATE libraries l
SET basement_bookshelf_id = (
    SELECT id FROM bookshelves
    WHERE library_id = l.id AND type = 'basement' LIMIT 1
);

-- 查询时永远排除 soft_deleted 的 Books
-- WHERE books.soft_deleted_at IS NULL
```

---

## 下步计划

### Phase 2: Repository + Models

- [ ] 更新 ORM Models（新增字段）
- [ ] 扩展 Repository 查询方法（get_by_bookshelf_id, find_in_basement_before 等）
- [ ] 编写数据库迁移脚本

### Phase 3: Service 详细实现

- [ ] LibraryService: 处理 BasementCreated 事件
- [ ] BookshelfService: delete_bookshelf 级联逻辑
- [ ] BookService: delete, restore, move, purge_basement 方法
- [ ] 权限检查和验证

### Phase 4: Router + API

- [ ] POST /books/{id}/move
- [ ] POST /books/{id}/restore
- [ ] DELETE /books/{id}（实际转移到 Basement）
- [ ] GET /libraries/{id}/basement（回收站查看）
- [ ] DELETE /libraries/{id}/purge-basement（清理）

### Phase 5: 测试

- [ ] 单元测试：Domain 层规则验证
- [ ] 集成测试：跨聚合操作
- [ ] E2E 测试：完整业务流程

---

## 架构对标

| 特性 | Wordloom v3 | Notion | Google Drive | Evernote |
|------|-----------|--------|-------------|----------|
| 聚合根 | 独立根 | 独立页面 | 独立文件 | 独立笔记 |
| 转移 | 真实转移 | 真实移动 | 真实转移 | 真实转移 |
| 删除 | Basement | 回收站 | 回收站 | 垃圾箱 |
| 恢复期 | 30 天 | 30 天 | 30 天 | 可配置 |
| 并发 | 低锁争用 | 页面独立 | 文件独立 | 笔记独立 |

---

## 设计决策理由

### 为什么是独立聚合根？

**问题：** 嵌套聚合（Library 包含 Bookshelf，Bookshelf 包含 Book，Book 包含 Block）

- 更新 Block 时需要锁定整个 Library 链（并发性能差）
- Book 对象可能包含数百个 Block（内存占用大）
- 查询单个 Block 需要先加载整个 Book→Bookshelf→Library

**解决：** 独立聚合根 + FK

- 每个聚合独立操作，无锁争用
- Block 编辑不涉及 Book/Bookshelf/Library（高并发）
- 查询任何对象都是 O(1) 按 ID 直接查

**成本：** Service 层变复杂

- 需要手动协调跨聚合操作
- 但这是合理的权衡（业务逻辑本就复杂）

### 为什么是 Basement 而非硬删除？

**问题：** 硬删除

- 用户误删除无法恢复（UX 差）
- 违反 GDPR 审计要求
- Book ID 变化，外部引用失效

**解决：** Basement（软删除 + 回收站）

- Book 转移到 Basement（bookshelf_id 变化）
- 记录 soft_deleted_at 时间戳
- 用户可恢复（restore_from_basement）
- 30 天后自动清理（符合隐私规范）

**成本：** 存储占用

- 但这是合理的（可定期清理）

### 为什么是真实转移而非复制？

**问题：** 复制+删除（Copy Semantics）

- Book ID 变化（外部链接失效）
- 两步操作（中间可能失败）
- 并发问题

**解决：** 真实转移（Move Semantics）

```python
book.move_to_bookshelf(new_id)
# 只是 UPDATE bookshelf_id = new_id（原子性）
```

- Book ID 不变（链接有效）
- 单 SQL 语句（原子性）
- 无并发问题

**成本：** 无

---

## 验证清单

- [x] Library domain.py: BasementCreated 事件 + basement_bookshelf_id
- [x] Bookshelf domain.py: BookshelfType + is_hidden + is_basement 方法
- [x] Book domain.py: library_id + soft_deleted_at + 转移方法
- [x] Block domain.py: 确认独立聚合根
- [x] DDD_RULES.yaml: 记录所有架构决策 + 规则更新
- [ ] Service 层: 待实现
- [ ] Models + Repository: 待实现
- [ ] 数据库迁移: 待实现
- [ ] API Router: 待实现
- [ ] 测试: 待实现

