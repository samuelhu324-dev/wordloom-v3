五、用 Wordloom 做“能加深记忆”的实验（建议你做 4 个，循序渐进）

下面四个实验都很短，但会让你对“索引/一致性/幂等”产生肌肉记忆。

实验 1：没有 search_index 的痛（基线）

目标：感受“直接在业务表 LIKE + JOIN 的痛苦”。

做法：

造数据：生成 5k～50k 个 blocks（可以用脚本或测试）

搜索：WHERE block.text ILIKE '%quantum%' + join tags

记录：

查询耗时

SQL 复杂度（你会开始加一堆条件）

你会得到一个结论：能用，但很快难用。

实验 2：做一张 search_index 投影表（统一实体 + 统一搜索入口）

目标：理解“search_index 不是索引结构本身，而是‘为了搜索而做的读模型’”。

结构建议（极简）：

entity_type（block/tag/book）

entity_id

text（可搜索纯文本）

snippet（展示用摘要）

updated_at

（可选）rank_score、tags_flat

然后：

你写 block/tag 时，同步写/异步写这张表

搜索接口只查 search_index 一张表

你会得到一个结论：统一入口 + 查询变简单。

实验 3：并发/乱序导致的“索引倒退”（你会一眼记住）

目标：亲手做出“索引倒退 bug”，然后用版本防倒退修掉它。

做法：

对同一个 block 连续产生两次更新事件：v1、v2

让 v2 先处理完，v1 后处理完（人为 sleep）

观察 search_index 最终变成 v1（倒退）

修法：加入版本或 updated_at 条件更新：

只有 incoming.updated_at >= current.updated_at 才更新

你会得到一个结论：异步系统必须面对乱序，防倒退是硬需求。

实验 4：Outbox + worker 的最小闭环（最终一致 + 可靠）

目标：把“索引更新”从用例事务里剥离出去，但保证不丢。

做法（极简）：

新建 outbox_events 表：event_id, type, payload, status, created_at

用例里：写 block + 写 outbox（同事务）

写一个 worker（甚至是一个定时循环脚本）：

拉取 pending outbox

更新 search_index

标记 sent

再故意制造失败：

让 worker 更新索引时抛异常 → 看它重试后能补上

重复投递同一个 event_id → 看去重/幂等是否生效

你会得到一个结论：Outbox 是跨系统一致性的“可靠传送带”。

