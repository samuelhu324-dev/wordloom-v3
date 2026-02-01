
3️⃣ Service 与 Repository 的职责划分问题

┌─────────────────────────────────────────────────────────────────┐
│  当前你的代码职责划分分析                                        │
└─────────────────────────────────────────────────────────────────┘

┌─ Service 层 ─────────────────────────────────────────────────┐
│ 当前做了什么：                                                │
│  ✅ create_book()                                            │
│  ✅ get_book(), list_books()                                 │
│  ✅ rename_book()                                            │
│  ✅ move_to_bookshelf() 权限检查                              │
│  ✅ delete_book() 软删除                                      │
│  ❌ 没有收集 Domain Events                                    │
│  ❌ 没有调用 EventBus 发布                                    │
│  ⚠️ 权限检查不够健壮（缺失 bookshelf_repository 时跳过）      │
│                                                               │
│ 缺失什么：                                                    │
│  ❌ Layer 1 Validation（业务规则检查）                         │
│     - 例如 create_book() 没有验证 bookshelf_id 有效性         │
│  ❌ Layer 4 Event Publishing（事件发布）                      │
│  ❌ 事务管理（UnitOfWork）                                     │
└──────────────────────────────────────────────────────────────┘

┌─ Repository 层 ──────────────────────────────────────────────┐
│ 当前做了什么：                                                │
│  ✅ save()                                                    │
│  ✅ get_by_id()                                               │
│  ✅ get_by_bookshelf_id()                                     │
│  ✅ delete()                                                  │
│  ✅ _to_domain() 转换                                         │
│  ❌ 没有 handle IntegrityError                                │
│  ❌ 没有 handle OptimisticLock                                │
│  ❌ _to_domain() 缺失 library_id 和 soft_deleted_at           │
│                                                               │
│ 缺失什么：                                                    │
│  ❌ Soft Delete 查询支持                                      │
│     - get_deleted_books()（Basement 检索）                   │
│  ❌ 错误处理和转译                                             │
│  ❌ 日志记录                                                  │
│  ❌ 并发控制（Optimistic Lock）                               │
└──────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

问题表现形式：

❌ create_book() 没有正确初始化 library_id
   └─ 导致 move_to_bookshelf() 权限检查失败
   └─ 导致 Bookshelf 删除时级联 Block 删除失败

❌ delete_book() 看起来对，但实际上：
   └─ basement_bookshelf_id 是从参数传入
   └─ 应该从 Library 查询获取，而不是外部传入！

❌ Repository 没有考虑 soft_deleted_at
   └─ 查询 Book 时可能返回已删除的 Book
   └─ 应该默认过滤 soft_deleted_at IS NULL

❌ 没有处理 Basement 中 Book 的查询
   └─ 恢复功能需要能查询 Basement（is_deleted=True）的 Books