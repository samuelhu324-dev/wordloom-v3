A. Block = 独立聚合根（推荐 80% 场景）

关系：Library、Bookshelf、Book、Block 都是各自的聚合根；Block.book_id 仅持有引用。

优点：

单个 Block 读写轻量，不必“加载整个 Book 的所有 Block”。

高并发编辑、协同场景更友好（每个 Block 独立事务）。

易于分片/缓存/增量渲染。

代价：

涉及“多个 Block 的整体操作”（例如大规模重排）变成跨聚合，一致性通常采用最终一致（借助“分数排序/fractional indexing”将需要更新的行数降到极少）。

适用：Notion/Confluence/CMS/大文档编辑器等——这是行业通行做法。

怎么锁，锁什么

每个聚合各自并发控制（按块上药）

把 Block 当作聚合根。编辑 Block 时，只对这条 Block 记录做并发控制，不触碰上层。

跨聚合的关系只用 ID 连接，不需要锁住对方。

首选乐观并发控制（Optimistic Concurrency）

在每个聚合表加 version（int）或 row_updated_at。

读取时带出版本；提交更新时带上版本做条件更新：
UPDATE blocks SET ... , version = version+1 WHERE id = :id AND version = :old_version;

没更新到行 ⇒ 说明被别人改过 ⇒ 返回 409 冲突，前端提示“有新版本，是否合并/覆盖”。

短时悲观锁，只在必要场景用

例如拖拽排序，要在很短的窗口内保证局部顺序不中断：
SELECT ... FROM blocks WHERE book_id=:b AND order_key BETWEEN :a AND :c FOR UPDATE;

锁的粒度是局部一小段，不是整本书，更不是整条链。操作完成立即提交。

避免“链式锁”与“级联事务”

不做“编辑 Block 时必须同时锁住 Book/Bookshelf/Library”的设计。

上层的统计数据（如块数、最后编辑时间）采用异步/最终一致的去规范化（denorm）更新，而非同事务强一致。

排序与协同编辑

排序：用 Fractional Indexing（可插值排序键，如 DECIMAL 或字符串）。把 A 与 B 之间的新块的 order_key 设为两者中间值，只有极少数情况下才需要小范围重编号（可异步）。

多人协同：

初期：块级并发 + 乐观锁已经足够。冲突概率低且可提示合并。

进一步：支持“租约式编辑”（editing lease），用 Redis 记一把 30–120 秒的租约。有人正在编辑该块时，别人看到“只读/抢占”提示。

实时协同（Google Docs/Notion 级）：再引入 OT/CRDT（如 Yjs/Automerge）针对 Block.content 这一个值对象做文本层同步，依然不影响聚合边界。

事务与一致性建议（Wordloom 版）

块编辑：单块事务 + 乐观锁。

批量重排：局部悲观锁（短时）+ 提交后广播变更。

计数/摘要（如 book.block_count、book.last_edited_at）：

同步快速写入一份事件（BlocksUpdated），

后台消费者异步更新 Book 的去规范化字段（几百毫秒内最终一致）。

媒体/标签：各自独立聚合；引用 ID，更新互不锁对方。

API 层：返回 ETag/If-Match 或 version 字段，前端据此做并发控制提示。

你可以照抄的实操清单

 给 blocks 表加 version INT NOT NULL DEFAULT 1（或 updated_at）索引。

 所有 UPDATE blocks 都带 WHERE id=:id AND version=:old_version。

 拖拽排序采用 order_key DECIMAL，插入取中值；必要时只锁局部范围 FOR UPDATE。

 books 的 block_count/last_edited_at 由异步任务更新（消费领域事件）。

 REST 返回 version/ETag；前端提交时带 If-Match 或 version。

 如需“正在编辑”提示，加一个 Redis SETNX block:{id}:lease <user> EX 60 的租约。

一句话定论：编辑 Block ≠ 锁整条父链。用“每聚合独立 + 乐观为主、悲观为辅 + 异步去规范化”，效率高、协同好、也最符合 DDD 的聚合边界原则。接下来如果你愿意，我可以把你当前的表结构/服务层补上 version 字段与条件更新示例，并给你一段拖拽排序的中值插入与局部锁示例，直接可用