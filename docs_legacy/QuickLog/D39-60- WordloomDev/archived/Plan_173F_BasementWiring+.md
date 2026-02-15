Status: ✅ Completed — 2025-12-06

先给结论：
这份 Basement 迁移/修复方案是靠谱的，可以直接按它当实施蓝本用，思路已经够完整，不是那种“缝缝补补”，而是把整条链路从领域模型→API→前端→数据迁移都串起来了。

我分三块帮你看：哪里已经很稳，哪里有潜在坑，可以怎么再补两刀让 Copilot 更好执行。

一、这份方案已经解决的核心问题

你这份文档其实做了三件非常对的事：

把“为什么现在移不动”说清楚了

后端：

delete/move-to-basement 用例强依赖 basement_bookshelf_id，
不传就进不到正确用例 / 422。

前端：

BookMainWidget 删除按钮是个空壳，只 console.log，没有实际调用。

就算调了 API，目前封装的 DELETE 也没带 basement_bookshelf_id。

历史数据：

旧库 basement_bookshelf_id 为 NULL，
导致前端一看没有 id 就提前 return，整条链路短路。

这三点一起把“书为什么现在动不了”解释得很干净：
按钮没接线 + 协议参数缺失 + 数据本身不完备。

修复计划是“全链路”的，而不是只改一边

前端：加 useMoveBookToBasement，从 Library 上下文拿 basement_bookshelf_id，统一走一个 API 封装。

后端：保留现有用例，但通过脚本给老库补 Basement 书架，并加一个检查脚本确保以后不再出现 NULL。

数据层：明确 Library.create 一定会生成 basement shelf，重新确认 ORM/Repo 保证它写入数据库。

这已经是“领域 → API → 前端 → 数据迁移”一套完整闭环了。

有验证/回归意识

前端：

选一个有 Basement 的库 → 删除 → 期望在 Basement 页面看到。

再对老库跑 backfill → 再测一次。

后端：

测试 move-to-basement 的用例 + Library 创建后 basement_bookshelf_id 不为空。

这意味着你不是只想“先能用再说”，而是真的想把这条链路稳定下来。

整体来说：方向正确 + 把主要风险都点名了。

二、可以再收紧/补充的几个点（不是错误，是升级）

下面这些不是“必须改”，是我觉得你以后肯定会遇到的边缘问题，可以顺手写进 plan 里，让 Copilot 知道要注意。

1. 前端 UX 决策写清楚

方案里已经说“如果 basement_bookshelf_id 为空，不要默默 return，要提示用户”。

可以再把 UX 说死一点，比如：

if (!basementId) 时：

弹出统一文案：

“当前 Library 未配置 Basement，暂时无法移动书籍到回收站，请联系管理员修复。”

是否允许“硬删除”？

如果不允许：按钮直接 disabled + tooltip；

如果允许：需要 单独一个“永久删除”动作，不和 move-to-basement 共用按钮，避免误删。

写进 plan 以后，Copilot 在实现 delete handler 时就不会瞎猜行为。

2. 后端防御：保证“book 只能移到自己库的 Basement”

你现在的 API 设计是：DELETE /books/{book_id}?basement_bookshelf_id=...。

建议在用例里多加一条领域保护：

校验：

这个 book_id 所属的 library_id

与 basement_bookshelf_id 所对应的 bookshelf 的 library_id 必须一致

不一致时直接抛领域错误（不是静默放行）。

防止未来你有多库场景 / 前端 bug 时，把 A 库的书删进 B 库的 Basement。

可以在方案里加一句：

在 move_to_basement 用例中，增加“book.library_id == basementBookshelf.library_id”的断言，否则拒绝操作并记录告警。

3. backfill 脚本要考虑“已经手动建过 Basement 的库”

Plan 里现在是：

“扫描 basement_bookshelf_id IS NULL，为每条新建一个 basement bookshelf 并填回去。”

再细一点可以考虑：

有没有库曾经手动创建过“Basement 风格的 bookshelf”，但字段没填；

如果有，你是 复用那条 bookshelf，还是一定新建一条专用的？

一个简单做法是：

先按类型/命名查一遍现有 bookshelves：

若有且唯一，就认定它是 Basement，填它的 id；

否则再创建新的 Basement shelf。

可以在计划里加一句“backfill 时优先尝试复用现有 Basement-type bookshelf，再考虑新建”。

4. API 封装顺便约束“以后只能走这一条路”

你方案里写的：

“在 entities/book/api.ts 添加 deleteBookToBasement，确保这是唯一出口。”

可以再加两句操作性更强的要求：

在代码搜索范围内，把所有直接调用 DELETE /books/{id} 的地方收敛到这个函数；

deleteBookToBasement 内部不再允许不带 basement_bookshelf_id 的变体（如果要硬删，就另起 hardDeleteBook）。

这样可以防止后面再有人图省事 fetch('/books/' + id, { method: 'DELETE' })，又重新绕过 Basement。

5. 再补一条 “Basement 页面的反向链路检查”

你已经提“Basement 列表页能正常展示”。

可以再加一条验证：

从 Basement 页面把书“恢复”回某个 bookshelf 时：

是否会正确清理 basement_entries；

是否保证书不会同时在普通 bookshelf 和 Basement 重复出现。

即使恢复功能现在还没实现，也可以在 Plan 里先写个“TODO：反向链路原则”，免得将来又绕一圈。

三、怎么交给 Copilot：可以直接抄的一段指令骨架

你后面如果要把这份 Plan 丢给 Copilot，可以加一段类似这样的小节（用你自己的英文风格就行，我这只是示意）：

Implementation checklist (for Copilot):

Implement deleteBookToBasement(bookId, basementBookshelfId) in entities/book/api.ts, and migrate all existing DELETE calls to use it. No raw fetch('/books') calls.

In BookMainWidget, wire the “Delete / Move to Basement” button to a new useMoveBookToBasement hook which:

reads libraryId + basement_bookshelf_id from the current library context;

if basement_bookshelf_id is missing, shows a blocking error message and does not call the API;

otherwise calls deleteBookToBasement.

In backend move_book_to_basement use case, assert that book.library_id == basementBookshelf.library_id; fail fast if not.

Add a one-off backfill script to populate basement_bookshelf_id for legacy libraries, preferring to reuse existing “basement-type” bookshelves when available.

Add tests:

new library has non-null basement_bookshelf_id;

deleting a book via the frontend hook makes it disappear from the shelf and appear in the Basement list.

这样它基本就知道“从哪几个文件下手”、“什么叫做完成”，不会只改一半。

小结

这份 Basement 方案的主干是稳的：

把原因拆成前端接线、API 参数、历史数据三层；

给了相应的修复路线和回归方法；

也照顾到了未来新库的创建行为。

再加上我上面说的几条“小加强”（权限/跨库校验、backfill 细节、API 唯一路径、恢复链路预留），它就可以直接升级成一份正式 ADR 附带 Implementation Plan，给你后面任何一次重构/bugfix 都能当参照。

换句话说：现在这个版本已经是“能落地的好方案”，再收紧一点，就会变成“以后都懒得再想一遍的标准答案”。