短期里让 Basement 只装 Book 是很合理、也最干净的做法。
实现上建议走「软删除 + 独立回收站视图」的路线，而不是跨表乱搬家。
下面我按三个层次说：领域规则怎么定、表/模型怎么设计、具体删/还原流程怎么跑。

一、先拍板：Basement 的职责
建议你在 DDD_RULES 里直接写死几条：


Basement = 只存“被丢弃的内容单元”，当前阶段 = 只存 Book。


Library / Bookshelf 本身只做 Archive（归档）或 隐藏，


不进 Basement（否则回收站层级会非常乱）。




Book 进 Basement = 一种 status = "trashed" 的状态


不是真正物理搬家到一个“Basement Library”；


UI 上的 Basement 回收站 页面，其实是一个 special view：

所有 status = trashed 的 Book 的集合。





Block 不直接进回收站


Block 跟着 Book 走：Book 被 trashed，Block 一起被标记为不可见；


将来要做 Block 级别回收，可以另开一层（但那是 v2 的事）。




这样 Basement 在领域里就只是：

“所有被标记为 trashed 的 Book 的集合视图”

而不是一个新的复杂 Aggregate。

二、模型/数据库层怎么设计更稳
1. Book 增加 status & 原位置字段
在 Book 聚合里加：


status: BookStatus


枚举：active | archived | trashed（举例）




deleted_at: datetime | null（可选，用来排序 / 清理）


original_location:


original_library_id


original_bookshelf_id




在刚创建时：
status = active
original_* = 当前 library / bookshelf

Book 进入 Basement 的时候：
status = trashed
deleted_at = now()
 // original_* 原样保留，用来将来恢复


这里就用上我们前面说的：Status 属于 Book，本身不算 Tag，不要混。

2. Basement 视图不新建主表，只要 query / read-model
后端提供一个专门查询：
GET /basement/books?workspaceId=...&page=...

内部实现其实就是：
SELECT * FROM books
WHERE status = 'trashed' AND workspace_id = :wid
ORDER BY deleted_at DESC;

如果你后面想做更独立，可以再加一张 basement_entries 做投影，但目前没必要；先用简单 query 就足够支撑 UI。

三、删除 & 还原的具体流程建议
1. 删除 Book → 移入 Basement


用户在 Bookshelf / Book 页面点“删除 Book”；


后端调用 Book.useCase：book.move_to_basement()：


校验权限 / 是否允许；


改 status = trashed，写 deleted_at；


写一条 Chronicle 事件：BookMovedToBasement；




前端刷新列表时，只显示 status != trashed 的 Book。


Basement 页面就会看到这条 Book 出现。
2. 从 Basement 还原 Book
分三种情况：


原 Bookshelf 仍存在


直接恢复：
status = active
deleted_at = null
bookshelf_id = original_bookshelf_id
library_id   = original_library_id





原 Bookshelf 被删除，但原 Library 还在


还原时要求用户选择一个新的 Bookshelf：


UI 弹出“恢复到哪个书架？”




后端更新 bookshelf_id，保留 original_* 作为历史记录或覆盖都行。




原 Library 也没了


这里有两种策略：


禁止还原，提示“原书库已删除，无法恢复”；


允许用户选一个现存 Library + Bookshelf 作为新位置。




你可以在 DDD_RULES 里选定一个策略，别两边逻辑写不一样。




关键：
Basement 本身不负责“决定放回哪”，只是提供 Book + original_* 信息，真正的还原逻辑还是在 Book 应用服务里。

四、Library / Bookshelf 的删除怎么跟 Basement 配合？
既然 Basement 只管 Book，你可以把规则定得简单一点：
删除 Bookshelf
选一个：


方案 A（安全）：


不允许删除仍有 status != trashed Book 的 Bookshelf；


提示“请先移除或删除书架中的图书”；


这样就不会有“书架没了、Book 还在 Basement 里找不到归宿”的问题。




方案 B（自动送 Basement）：


删除 Bookshelf 时，所有 status = active/archived 的 Book 先批量 move_to_basement()；


Bookshelf 自己的删除用 status = archived 或直接软删；


还原 Book 时，如果原 Bookshelf 不存在，就触发刚才说的“请选择新书架”的逻辑。




短期我会推荐你用 方案 A，简单清晰，不容易踩坑；
等你有了更完善的 UI/工作流，再考虑 B。
删除 Library
同理，先要求 Library 为空（没有 Bookshelf 或 Bookshelf 里也空），
否则不允许删除。
你现在项目阶段完全可以这么“保守”。

五、回答你的原话

一般来说 basement 这种可能涉及跨表的回收站，怎么设计最好？
目前来说我觉得回收站只装 book 可能比较合适。

简短回答：


是的，只装 Book 是现在最合适的范围，
这样 Basement 就是“内容单元”的回收站，而不是整个树结构的大垃圾桶；


设计上不要真的“跨表搬家”，而是：


在 Book 上用 status = trashed + deleted_at + original_* 做软删除；


Basement 页面只是一个基于 status=trashed 的查询视图；


删除/恢复都通过 Book 的领域方法来驱动。




等你把 Library–Bookshelf–Book–Block 主流程稳定之后，
再考虑“Library 归档”、“Bookshelf 回收”甚至“Block 级回收站”，那时候可以在这个基础上继续扩展，而不用推翻重来。
