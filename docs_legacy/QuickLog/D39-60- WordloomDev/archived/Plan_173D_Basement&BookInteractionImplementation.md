Status: ✅ Completed — 2025-12-06

Plan：基于 Plan173C 的 Basement–Book 集成落地
简要结论：
Plan173C 和当前实现大体同向——Book 仍是“真源”，Basement 已有独立模块和恢复/硬删用例；差异主要在于：删除入口还没完全“视为回收站”，以及现在 Basement 用例依赖事件总线风格稍重。下面是一份在不大改聚合、不上复杂 EventBus 的前提下，可执行的最小实现计划。

Steps
统一删除入口 → Book Delete 用例里显式“丢进 Basement”
1.1 在 book_router.py 中确认/收敛删除路由（如 delete_book）只走一个用例（例如 DeleteBookUseCase）。
1.2 在对应用例（backend/api/app/modules/book/application/use_cases/...DeleteBookUseCase）中：保持现有软删除/状态标记逻辑（book.mark_as_deleted() / book.move_to_basement() 一类），然后在保存成功后，同步调用 Basement 用例，例如：通过 di.get_move_book_to_basement_use_case() 构造 MoveBookToBasementCommand(book_id, basement_bookshelf_id, reason)，完成“删除 = 软删 + 记一条 BasementEntry”的组合动作。

让 Basement 用例成为“回收站操作代理”，少依赖事件总线
2.1 在 move_book_to_basement.py、restore_book_from_basement.py、hard_delete_book.py 中，确保它们的职责是：

通过 BookRepository 找到 Book；
调用已有领域方法（例如 book.move_to_basement(...) / book.restore_from_basement(...) / book.hard_delete(...)）；
保存 Book；必要时记录 Basement 快照（BasementBookSnapshot），作为查询视图。
2.2 将这些 use case 对事件总线 / DomainEvent 的依赖收紧为“可选扩展”：保留发布逻辑，但通过 DI 传入 Optional[EventBus] = None，默认不注入即可达成“能运行但不强制 CQRS”。
把 Book 的 Basement 状态定义锁死为“单一真源”
3.1 在 backend/api/app/modules/book/domain/entities.py（或等价文件）中确认/补齐：

状态枚举含 BASEMENT 或有 is_in_basement 之类派生属性；
提供对外方法 mark_as_basement(now)、restore_from_basement(now) 等，仅修改自身字段、不碰 Basement 存储。
3.2 在 Basement 侧（entities.py）中，BasementBookSnapshot 只存快照字段（book_id/library_id/bookshelf_id/title/moved_at/...），不额外引入“第二套状态”，所有状态判断都通过 Book 的字段或只读快照解释。
恢复/硬删链路：从 Basement 回到 Book 的“薄服务调用”
4.1 在 basement_router.py 中检查 /books/{book_id}/restore-from-basement 与 DELETE /books/{book_id}：

路由只负责解析参数 → 调用 RestoreBookFromBasementUseCase / HardDeleteBookUseCase；
不直接操作仓储，所有业务放在 use case。
4.2 在对应 use case 中：
Restore: 调用 Book 的 restore_from_basement(target_bookshelf_id)（或等价方法）+ 保存；然后删除/更新 Basement 快照记录；
HardDelete: 先让 Book 聚合真正删除（book.hard_delete() 或直接仓储删除），再清理 Basement 快照；
这样“书的生死决策”完全留在 Book 模块，Basement 只负责发起这些动作并保证列表干净。
通过一个小的“桥接服务”避免模块互相穿透
5.1 在 Book 模块下新建一个轻量服务（例如 backend/api/app/modules/book/application/services/basement_bridge.py）：

暴露方法：send_to_basement(book: Book, di: DIContainer)、restore_from_basement(book_id: UUID, target_shelf: UUID | None, di: DIContainer) 等；
内部只是调用 Basement 的 use case（通过 DI 拿到 MoveBookToBasementUseCase / RestoreBookFromBasementUseCase）。
5.2 DeleteBookUseCase 和其它需要联动 Basement 的用例只依赖这个 bridge，而不直接 import Basement 的领域/仓储；Basement 侧也只依赖 BookRepository + 域方法，保持“书在核心域，Basement 是围绕它的应用服务”。
API 级别明确分工：管理端看 Basement，普通端看 Book
6.1 保持 basement_router.py 放在 /admin/... 下，仅提供：列表 /libraries/{library_id}/basement/books、恢复 /books/{book_id}/restore-from-basement、硬删 DELETE /books/{book_id}。
6.2 book_router 面向普通操作（创建/编辑/删除）继续使用原有路径，内部是否同步写 Basement 由用例+bridge 决定，对外 API 不暴露 Basement 细节。这样前端 admin Basement 页面只打 Basement 路由，普通书页只打 Book 路由，职责边界在 URL 层也清晰。

如果你愿意，下一步我可以按这份计划，把第 1 步和第 4 步需要调整的 use case / router 文件点出来更细一点（逐文件 TODO 列表），方便你逐项实现或让我帮你改。