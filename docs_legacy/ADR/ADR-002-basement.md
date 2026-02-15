  AD-002:
    title: "Basement 模式（软删除 + 回收站）"
    description: |
      不硬删除用户数据，而是转移到特殊的 Basement Bookshelf（回收站）。
      - 每个 Library 自动创建一个隐藏的 Basement Bookshelf
      - 删除 Book 时，不是硬删除，而是 move_to_bookshelf(basement_id)
      - 用户可在 Basement 中恢复 Book（restore_from_basement）
      - 30 天后自动清理（由外部 Job 处理）

    benefits:
      - 用户可恢复误删除（UX 优化）
      - 符合 GDPR/隐私规范（软删除审计日志）
      - 实现简单（只是书架转移）
      - Book ID 不变（链接不失效）

    tradeoffs:
      - 占用存储空间（需定期清理）
      - 普通查询需 WHERE soft_deleted_at IS NULL
      - 用户端需显示 Basement 逻辑（可选）

    implementation:
      - bookshelf/domain.py: 新增 BookshelfType.BASEMENT, is_hidden 字段
      - book/domain.py: 新增 soft_deleted_at 字段，move_to_basement() 方法
      - library/domain.py: BasementCreated 事件
      - book/service.py: delete_book(), restore_book(), purge_basement() 方法

    related_rules:
      - RULE-010
      - POLICY-006

    industry_examples:
      - Notion (回收站)
      - Google Drive (回收站)
      - Evernote (垃圾箱)
      - OneNote (回收站)
