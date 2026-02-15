  AD-004:
    title: "辅助功能分层（Auxiliary Features Layering）"
    description: |
      将 pin/unpin/favorite/archive 等非核心业务功能从 Domain 层移到 Service 层。
      - Domain 层保留：rename(), change_status(), move_to_bookshelf(), restore_from_basement()
      - Service 层拥有：pin(), unpin(), favorite(), unfavorite(), archive(), unarchive()
      - Service 直接修改聚合根字段，不发送事件

    rationale: |
      Core vs Auxiliary Features 分类：
      1. Core Features（Domain 层）:
         - 改变业务不变性的操作（rename, move, restore）
         - 需要事件溯源的操作（BookMovedToBookshelf, BookRestoredFromBasement）
         - 涉及跨聚合协调的操作（move_to_basement）

      2. Auxiliary Features（Service 层）:
         - UI 便利性功能（pin, favorite, archive）
         - 不改变核心状态的操作（is_pinned, is_favorite）
         - 不需要事件的幂等操作

    benefits:
      - Domain 层保持简洁（30-40% 代码量）
      - Service 层承担业务编排（20-25% 代码量）
      - 事件数量减少（只记录核心变更）
      - Code weight 平衡

    tradeoffs:
      - Auxiliary features 不能通过事件追踪历史
      - 需要明确的 Domain vs Service 分界线
      - 若后续需要 pin/favorite 历史，需要重构到 Domain

    implementation:
      - bookshelf/domain.py: 删除 pin/unpin/favorite/unfavorite/archive/unarchive 方法
      - bookshelf/service.py: 新增 pin_bookshelf/unpin_bookshelf/favorite_bookshelf 等方法
      - book/domain.py: 删除 pin/unpin/archive 方法
      - book/service.py: 新增 pin_book/unpin_book/archive_book 等方法

    events_removed:
      - BookshelfPinned (Unpinned, Favorited, Unfavorited) - moved to Service
      - BookPinned (Unpinned) - moved to Service
      - These are not core domain events anymore

    related_rules:
      - RULE-007, RULE-008 (Bookshelf auxiliary state)
      - RULE-015, RULE-016 (Book auxiliary state)
