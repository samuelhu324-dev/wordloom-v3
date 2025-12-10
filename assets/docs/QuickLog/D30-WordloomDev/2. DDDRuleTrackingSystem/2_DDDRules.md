# ============================================
# Wordloom v3 DDD 规则追踪系统
# ============================================

metadata:
  version: "3.0"
  domain_model: "Library → Bookshelf → Book → Block"
  created_at: "2025-11-10"
  last_updated: "2025-11-10"

# ============================================
# Domain 1: Library（图书馆 - 聚合根）
# ============================================
domains:
  library:
    name: "Library（图书馆）"
    type: "AggregateRoot"
    description: "Wordloom 用户的唯一图书馆入口，所有书架、书籍、块的容器"

    invariants:
      RULE-001:
        title: "用户只有一个 Library"
        statement: "每个 User 只能拥有一个 Library，通过菜单栏'Library'入口进入"
        type: "invariant"
        priority: "critical"
        status: "planned"

        # 代码实现位置
        implementation:
          domain_file: "backend/api/app/modules/library/domain.py"
          test_file: "backend/api/app/tests/test_library/test_invariants.py"

        # 验证方法
        validation:
          method: "pytest"
          test_case: "test_library_single_per_user"

        # 关联
        related_files:
          - "backend/api/app/modules/library/repository.py"
          - "backend/api/app/modules/library/service.py"

        # DevLog 追踪
        devlog_entry: "D30-Library-SingleInstance"
        pr_number: null  # 待提交

      RULE-002:
        title: "Library 拥有唯一标识"
        statement: "Library 必须有 UUID id 和用户唯一的名称"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/library/domain.py"
          test_file: "backend/api/app/tests/test_library/test_invariants.py"
        devlog_entry: "D30-Library-Identity"

    policies:
      POLICY-001:
        title: "Library 级联删除策略"
        statement: "删除 Library 时，级联删除其下所有 Bookshelf、Book、Block"
        type: "policy"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/library/domain.py"
          test_file: "backend/api/app/tests/test_library/test_policies.py"
        devlog_entry: "D31-Library-Cascading"

    # Library 的子聚合
    children:
      - bookshelf

# ============================================
# Domain 2: Bookshelf（书架 - 子聚合）
# ============================================
  bookshelf:
    name: "Bookshelf（书架）"
    type: "AggregateRoot"  # 可以独立存在，但通常在 Library 下
    description: "用户可无限创建的书架，用于组织和分类书籍"
    parent: "library"

    invariants:
      RULE-003:
        title: "Bookshelf 可无限创建"
        statement: "用户可在 Library 下无限创建 Bookshelf，无数量限制"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/bookshelf/domain.py"
          test_file: "backend/api/app/tests/test_bookshelf/test_invariants.py"
        devlog_entry: "D32-Bookshelf-Unlimited"

      RULE-004:
        title: "Bookshelf 必须属于一个 Library"
        statement: "每个 Bookshelf 必须持有其所属 Library 的 ID，不能孤立存在"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/bookshelf/domain.py"
        devlog_entry: "D32-Bookshelf-BelongsToLibrary"

      RULE-005:
        title: "Bookshelf 内书籍可无限添加"
        statement: "每个 Bookshelf 可持有无限数量的 Book"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/bookshelf/domain.py"
        devlog_entry: "D32-Bookshelf-UnlimitedBooks"

    policies:
      POLICY-002:
        title: "Bookshelf 删除策略"
        statement: "删除 Bookshelf 时，级联删除其下所有 Book 和 Block"
        type: "policy"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/bookshelf/domain.py"
        devlog_entry: "D33-Bookshelf-CascadingDelete"

    children:
      - book

# ============================================
# Domain 3: Book（书籍 - 子聚合）
# ============================================
  book:
    name: "Book（书籍）"
    type: "AggregateRoot"
    description: "用户可在 Bookshelf 下无限创建的书籍，作为 Block 的容器"
    parent: "bookshelf"

    invariants:
      RULE-006:
        title: "Book 可无限创建"
        statement: "用户可在 Bookshelf 下无限创建 Book，无数量限制"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/book/domain.py"
        devlog_entry: "D34-Book-Unlimited"

      RULE-007:
        title: "Book 必须属于一个 Bookshelf"
        statement: "每个 Book 必须持有其所属 Bookshelf 的 ID"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/book/domain.py"
        devlog_entry: "D34-Book-BelongsToBookshelf"

      RULE-008:
        title: "Book 内块可无限添加"
        statement: "每个 Book 可持有无限数量的 Block"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/book/domain.py"
        devlog_entry: "D34-Book-UnlimitedBlocks"

    policies:
      POLICY-003:
        title: "Book 删除策略"
        statement: "删除 Book 时，级联删除其下所有 Block"
        type: "policy"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/book/domain.py"
        devlog_entry: "D35-Book-CascadingDelete"

    children:
      - block

# ============================================
# Domain 4: Block（块 - 值对象）
# ============================================
  block:
    name: "Block（块）"
    type: "ValueObject"  # 块是最小单位，通常不独立存在
    description: "Book 的最小单位，可以是文本、图片、代码等多种类型"
    parent: "book"

    invariants:
      RULE-009:
        title: "Block 可无限创建"
        statement: "用户可在 Book 下无限创建 Block，无数量限制"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/block/domain.py"
        devlog_entry: "D36-Block-Unlimited"

      RULE-010:
        title: "Block 必须有类型"
        statement: "每个 Block 必须有 type（text/image/code/table 等）"
        type: "invariant"
        status: "planned"
        implementation:
          domain_file: "backend/api/app/modules/block/domain.py"
        devlog_entry: "D36-Block-MustHaveType"

# ============================================
# 关键业务事件（Domain Events）
# ============================================
domain_events:
  LibraryCreated:
    description: "用户创建了 Library（通常由系统自动创建）"
    aggregate: "library"
    fields:
      - user_id: UUID
      - library_id: UUID
      - created_at: datetime

  BookshelfAdded:
    description: "添加了新的 Bookshelf"
    aggregate: "bookshelf"
    fields:
      - library_id: UUID
      - bookshelf_id: UUID
      - name: str

  BookAdded:
    description: "添加了新的 Book"
    aggregate: "book"
    fields:
      - bookshelf_id: UUID
      - book_id: UUID
      - name: str

  BlockAdded:
    description: "添加了新的 Block"
    aggregate: "block"
    fields:
      - book_id: UUID
      - block_id: UUID
      - block_type: str

# ============================================
# 实现计划（按优先级）
# ============================================
implementation_plan:
  phase_1_core:
    - RULE-001  # Library 单实例
    - RULE-003  # Bookshelf 无限创建
    - RULE-006  # Book 无限创建
    - RULE-009  # Block 无限创建

  phase_2_relationships:
    - RULE-002  # Library 标识
    - RULE-004  # Bookshelf 属于 Library
    - RULE-007  # Book 属于 Bookshelf

  phase_3_policies:
    - POLICY-001  # Library 级联删除
    - POLICY-002  # Bookshelf 级联删除
    - POLICY-003  # Book 级联删除