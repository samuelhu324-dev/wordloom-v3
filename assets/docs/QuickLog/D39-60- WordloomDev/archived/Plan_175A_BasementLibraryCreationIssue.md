Status: ✅ Completed — 2025-12-07

Completion Notes:
- `CreateLibraryUseCase` 现在在同一 AsyncSession 内调用 `_ensure_basement_bookshelf()` 创建 Basement 书架，并把 `basement_bookshelf_id` 带回响应，彻底移除了 “库已建好但 Basement 缺失” 的窗口。
- Mock/SQLAlchemy 仓储都会先复用 legacy Basement，再按 Library 内置的 ID 创建新书架；新测试覆盖了“首次创建/复用”两条路径。
- DDD/Hexagonal/Visual 规则与 ADR-158 同步记载本不变式，前端不再隐藏 Basement CTA，Plan175A 标记完成。

先把结论说死：
选“提前有书架”这条路，Copilot 那段话整体方向是对的，你可以顺着它往前推一把。
懒创建（NULL + 第一次删除时再造书架）在你现在这个结构里是自找麻烦。

1. 先回答：到底要不要一开始就有书架？

从你现在的模型来看：

libraries.basement_bookshelf_id 是 必填外键，指向 bookshelves；

领域规则其实已经在暗示：

每个 Library 一直都应该有且只有一个 Basement 书架。

如果你改成：

允许 NULL，然后第一次“移动到回收站”时再懒创建书架，

那会导致：

领域层多了一种“半残状态”

Library 创建完但没有 Basement

一堆用例都要判断：

“如果没有 Basement 就先建一个，再干正事”

一半逻辑要容忍 None，一半逻辑假设“肯定有”，非常容易乱。

多个层级都被迫感知这个“例外”

实体 / 仓储：要处理 Optional[UUID]

应用服务：每次删除书都要判断要不要“顺便创建 Basement”

API DTO：字段要么可空要么分两种模式

前端：要处理 “没有 basementId 就不能调 API / 要先请求修复”
这就是 Copilot 说的“波及实体、仓储、应用服务、API DTO、前端查询等多层结构，属于大改”的意思，其实是对的。

还有并发/竞态问题

两个请求几乎同时第一次删除书：

A 请求创建了 Basement

B 请求也以为没有，重复建一条

然后你得在 DB 上搞 unique/constraint 来兜底，越搞越复杂。

反过来，如果你坚持：

Library 这个聚合的不变式：
“创建成功的 Library，一定有一个 Basement 书架，basement_bookshelf_id 永远非空。”

好处是：

领域模型简单：所有用例都可以假设 Basement 存在；

API 简单：

可以只传 libraryId，在服务器内部查 basement_bookshelf_id；

前端不用关心 null、不用兜各种 fallback；

你现在遇到的那些“因为 NULL 导致 move-to-basement 失效”的 bug，直接从源头消失。

所以从 DDD + 工程复杂度角度看，提前创建 Basement 书架是完全正确的选择，跟你直觉一致。

2. 怎么评估 Copilot 的这段话？

截图里的意思拆开就是：

既然 libraries.basement_bookshelf_id 现在是必填外键，
要改成“先有库、再有书架”就得要么去掉外键、要么允许 NULL，然后到处懒加载 —— 这是大改，不推荐。

更稳的办法是在“新建 Library 的用例”里，

自动先创建一个书架记录（它叫“基础书架”，你可以理解成 Basement 或默认可见书架），

拿到 bookshelf_id 后再写入 Libraries 表，

事务里一起提交。

因此“默认一开始就要有书架 / 立即创建一个书架”是最小改动方案。

这个判断我完全赞同，方向上没问题。
唯一要细化的是：你要区分：

系统的 Basement 书架（用于回收站逻辑，一般隐藏）

用户可见的“第一块书架”（例如“Default Shelf”）

你现在讨论的是前者（basement_bookshelf_id），
Copilot 提的“基础书架”有点混在一起，但实现思路是一致的：

“创建 Library 用例 = 在一个事务里：
创建 Basement Bookshelf（和可见默认书架，按你需要） → 用返回的 id 写入 Library。”

3. 具体怎么“投喂”给 Copilot？（可以直接复制改一改）

你可以给 Copilot 一段非常操作性的指令，重点是别让它去动表结构，而是实现‘创建 Library 时自动建 Basement 书架’。

比如这样写（你按项目语言改下名字就行）：

目标：保持 `libraries.basement_bookshelf_id` 为非空外键，
并保证每个 Library 从创建那一刻起就有一个 Basement 书架。

请按下面步骤修改后端：

1. 在领域层（Library 聚合的创建用例 / Application Service）中，
   把“创建 Library”改成两步、同一事务内完成：
   a) 调用 Bookshelf 仓储创建一个新的 bookshelf 记录：
      - type 或 role 标记为 'basement'
      - is_visible = false（Basement 对用户隐藏）
      - 关联当前 Library 所属的 owner / workspace
   b) 使用返回的 bookshelf.id 作为 `basement_bookshelf_id`，
      创建 Library 实体并持久化。
   要保证这两步在一个事务里提交，失败时回滚。

2. 对已有数据写一个 backfill 脚本 / migration：
   - 查找所有 `libraries` 中 `basement_bookshelf_id IS NULL` 的记录；
   - 对每一条：
     - 如果已经存在一个 type='basement' 且 library_id 匹配的 bookshelf，就复用它；
     - 否则新建一个 bookshelf（同样标记为 'basement'），
       并把它的 id 写回该 library 的 `basement_bookshelf_id`。
   - backfill 完成后，可以考虑在 DB 层加 NOT NULL + 外键约束。

3. 在 move-to-basement 用例里，禁止前端直接传 `basement_bookshelf_id`：
   - 入参只接收 `libraryId` 和 `bookId`；
   - 在用例内根据 `libraryId` 加载 Library，再从实体属性里取 `basement_bookshelf_id`。
   - 同时断言：book.library_id == library.id。

4. 为新逻辑补充测试：
   - 新建 Library 后，`basement_bookshelf_id` 一定非空，且指向 type='basement' 的 bookshelf；
   - 对一个已有 Library 调用“移动 Book 到 Basement”时，
     Book 会从原 bookshelf 移除，并出现在 Basement 里。


如果你还想顺便自动创建“第一个可见书架”，可以在第 1 步再加：

可选：在创建 Library 时，同时创建一个 type='default' 且 is_visible=true 的 bookshelf，
作为用户看到的第一个书架。Library 本身可以不保存它的 id，
前端通过 bookshelf 列表接口获取。


这样 Copilot 会非常明确：

表结构不要动

Basement 书架必须在 Library 创建时就存在

具体代码改哪里（创建用例 + backfill + 用例测试）

4. 简单总结一口气版

在你现在这个模型里，“懒创建 Basement + 允许 NULL”是把简单问题搞复杂；

把 Basement 当作 Library 聚合中的强不变式，
→ “Library 一旦存在，就必须有 Basement 书架”，
→ 是最符合 DDD、也最省心的做法；

Copilot 的建议基本就是朝这个方向走，你要做的，是帮它把需求写细：

创建 Library 的用例里自动建 Basement（+ 可见默认书架，按你需求），

用 backfill 修老数据，

move-to-basement 只依赖 library.basement_bookshelf_id，前端不再传 id。

这样“提前有一个书架”就不只是直觉，而是写进模型和代码里的硬规则了。