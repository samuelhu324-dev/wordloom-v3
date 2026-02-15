  AD-003:
    title: "真实转移而非复制（Move Semantics）"
    description: |
      Book 跨 Bookshelf 转移时，采用真实转移（UPDATE），而非复制+删除。
      - Book.move_to_bookshelf(new_bookshelf_id) 只是 UPDATE bookshelf_id
      - Book ID 不变，所有引用保持有效
      - 原子性强（单 SQL 语句）
      - 不生成新 ID

    benefits:
      - 原子性强，无中间失败状态
      - Book 只有一份（内存/存储高效）
      - 历史追踪简单（BookMovedToBookshelf 事件）
      - 用户链接始终有效

    tradeoffs:
      - 原来 Bookshelf 中的 Book 引用失效（需用 Repository 查询）
      - 不支持"一份 Book 在多个 Bookshelf"（Reference 模式不适用此项目）

    implementation:
      - book/domain.py: move_to_bookshelf(new_bookshelf_id) 方法
      - book/service.py: move_book_to_bookshelf() 协调逻辑

    related_rules:
      - RULE-011
      - POLICY-005

    industry_comparison:
      - Notion (真转移)
      - Google Drive (真转移)
      - 所有现代文件管理系统 (真转移)
