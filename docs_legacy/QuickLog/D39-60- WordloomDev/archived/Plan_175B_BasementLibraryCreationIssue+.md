Status: ✅ Completed — 2025-12-07

Completion Notes:
- `_ensure_basement_bookshelf()` 先查询同库的 BASEMENT 类型书架并复用现有 ID，只有缺失时才调用 `Bookshelf.create_basement()`，避免 legacy 数据重复建 Shelf。
- CreateLibraryUseCase 的 save、Basement save、响应 DTO 同步发生，任一失败会整体回滚，彻底移除 FK 漏洞与 500。
- `test_library/test_application_layer_simple.py::test_create_library_reuses_existing_basement` 锁死复用路径，文档/ADR-158 也记录了 Plan175B 的 Guardrail。

Plan 175B 的核心就是把 “每个新 Library 一定自带一个默认 Basement 书架（比如叫 Shelf）” 写死在模型和用例里，并把现在这个“创建库成功但 Basement 为空 / 抛 500”的过渡状态彻底消掉。

下面是按层次拆好的改造计划，你可以直接当 Checklist 用：

一、领域层：确保 Library 天生有 Basement 槽位

确认并锁定不变式：Library 的 basement_bookshelf_id 永远非空，代表“这个库对应的 Basement 书架的 ID”。

保留现有 Library.create 里生成 basement_id = uuid4() 的逻辑（你现在已经在这么做）。
明确约定：这个 ID 一定会在创建流程中对应到一条真实的 Bookshelf 记录。
补充命名约定：约定默认 Basement 的显示名为 "Shelf"（或你更想要的文案，比如 "Basement" / "回收站"），但这个名字只是 Bookshelf 的属性，不写死在 Library 里，只在创建 Basement 时用。

二、Bookshelf 领域 + 仓储：提供创建 Basement 的能力

在 bookshelf 模块里确认/增加一个创建工厂，支持创建 Basement 类型：

在 Bookshelf.create(...) 的基础上，允许传入 type_=BookshelfType.BASEMENT。
如果你想更语义化，可以加一个静态方法：
Bookshelf.create_basement(library_id: UUID, name: str = "Shelf")
内部调用 Bookshelf.create(..., type_=BookshelfType.BASEMENT)。
在基础仓储实现 infra/storage/bookshelf_repository_impl.py 中保证：

save(bookshelf) 能正常插入 Basement 类型的书架。
如果已经存在同一 library_id 的 Basement，可以抛 BookshelfAlreadyExistsError，但要修好构造函数（带默认 name 或全部通过 keyword 传参），避免之前那个 missing 1 required positional argument: 'name' 的 TypeError。
三、应用层：在 CreateLibraryUseCase 里“顺带创建 Basement 书架”

定位 CreateLibraryUseCase（在 api/app/modules/library/application/use_cases/create_library.py）：

它现在应该已经依赖 ILibraryRepository 和 IBookshelfRepository，并有一个 ensure_basement_bookshelf(library) 之类的私有方法（你之前堆栈里出现过）。
改造 use case 执行流程（伪代码）：

校验请求（user_id、name 等）。
调用 Library.create(user_id, name, ...) 得到 library（这里已经有 library.basement_bookshelf_id）。
在同一个 use case 流程中调用 ensure_basement_bookshelf(library)：
如果仓储里已经存在对应 Basement（极少见，主要是容错），直接略过或抛 BookshelfAlreadyExistsError。
否则通过 Bookshelf.create_basement(library_id=library.id, name="Shelf") 构造聚合。
调用 bookshelf_repository.save(basement).
顺序建议：
要么先创建 Library 再创建 Bookshelf，并让外层事务负责一起提交；
要么（取决于你现有事务管理）在同一个 async session 里先 save(basement) 再 save(library)，但这时 library.basement_bookshelf_id 要用 Basement 的 id（保持你现在的一致性）。
最后返回包含 library_id 和 basement_bookshelf_id 的 Response DTO。
异常处理策略：

正常情况下，第一次创建库不会触发 BookshelfAlreadyExistsError。
如果因为历史数据或并发，检测到同库已有 Basement：
Option A（简单）：捕获 BookshelfAlreadyExistsError，写 warning log，但继续使用已存在 Basement 的 ID，不再让请求失败。
Option B（更严格）：把这个异常包装成 500/409 并返回给前端，但必须保证事务整体回滚，避免“库创建成功但无 Basement”的半残状态。
四、API 层 / Router：保证事务和错误映射正确

在 library_router.py 的 create_library 路由中检查：

是否已经将 ILibraryRepository 和 IBookshelfRepository 注入到 CreateLibraryUseCase。
是否使用统一的事务装饰器 / AsyncSession 上下文。如果没有，建议把 “保存库 + 保存 Basement” 放在同一数据库事务内（FastAPI 依赖注入里通常是同一个 session）。
确认异常映射：

BookshelfAlreadyExistsError、LibraryAlreadyExistsError 等 DomainException 应该被全局异常处理器转换为结构化 JSON + 正确 HTTP 状态（409/422 等），而不是漏成原生 Traceback（你之前看到的 TypeError 就是还没走到这一层）。
五、前端契约：让 UI 能拿到 basementId 并正确展示

检查 POST /api/v1/libraries 的响应 DTO（在 CreateLibraryResponse 或相关 schema 里）：
已经包含 basement_bookshelf_id 字段；
前端 store / React query 接收到后写入库对象。
在 Basement 页面（你截图里的 “回收站”）确保：
通过当前 library 的 basement_bookshelf_id 去拉书 / 书架信息，而不是再依赖某些 NULL 容错逻辑。
之前为了兼容 NULL 加的 fallback（比如“如果没有 basementId 就隐藏入口/不请求”）可以逐步移除。
六、测试与回归

在 test_application_layer_simple.py / test_application_layer.py 中新增或确认已有用例：

“创建库时会自动创建名为 Shelf 的 Basement 书架，并保存到 bookshelf 仓储里”；
“重复创建同一库不会重复建 Basement（或按你的设计返回冲突）”；
“ListBasementBooksUseCase 在新库上返回空列表但不报错”。
运行至少以下测试：

如果你愿意，我可以下一步直接在仓库里帮你把 CreateLibraryUseCase.ensure_basement_bookshelf 和相关仓储改完，然后把对应测试补齐，你只要在本地重启 backend + 刷新前端验证就行。要直接动代码吗？