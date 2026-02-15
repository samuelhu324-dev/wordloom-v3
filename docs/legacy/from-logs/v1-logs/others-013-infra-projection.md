1) 截图1：对，刚刚基本就是把 search_index 这条链路“收口”了

你做的事情，本质上是把 event bus 入口的事务边界从：

“每个 handler 自己 commit/rollback（到处散落）”

变成：

“统一由 wrapper / registry（入口层）commit/rollback（集中管理）”

而且你顺手修了两个很关键的地雷：

重复 handler 定义导致注册/执行不确定

async def 里用同步 Session 导致阻塞风险（改成 AsyncSession）

所以是的：这个阶段的收口主要发生在 search_index_handlers（投影/索引更新那条事件链路）。其它模块（比如 repo 层自己的 commit/rollback）还没完全收口，这也是你路线 B 的 XFAIL 还在的原因。

2) 截图2：并发顺序/一致性（串行或防倒退）算在哪个模块？

这块通常不属于 domain，也不属于 repo，更不该丢给 handler 里零散 if/else。它属于：

infra（基础设施）里的“投影更新/事件消费策略”
或者叫 event processing / projection consistency strategy

更具体一点，你现在讨论的是 search_index 这种 read model / projection 的一致性问题，所以它最自然的落点是：

infra/event_bus/...（事件消费层面的并发控制）

或 infra/projections/search_index/...（专门放投影逻辑的模块）

如果你已经有 infra/search/、infra/indexing/ 之类目录，也可以放那儿，但核心思想不变：它是投影侧的基础设施策略。

两种“保险栓”分别放哪最合适？
A) “按 entity_id 串行”（keyed serialization）

这是消费/调度策略，最像 event bus 的责任：

event bus 在调用 handlers 前，先按 entity_id 把同一实体的事件排队串行执行

不同实体仍可并发

👉 放在 infra/event_bus/dispatcher 或你现在的 registry/wrapper 那一层最顺。

B) “版本号防倒退更新”（anti-stale / monotonic update）

这是投影写入策略，最像 projection 自己的责任：

handler 写 DB 时加条件：只有 incoming_version >= current_version 才更新

或用 updated_at 做比较

👉 放在 infra/projections/search_index（或者 search_index handler 里生成 SQL 的那层）最顺。

给你一句“定位口诀”（以后不迷路）

管并发怎么跑（排队/限流/串行）→ event bus / dispatcher（infra）

管写入怎么不倒退（版本判断/条件 update）→ projection 写入逻辑（infra/projection）

domain 只关心“发生了什么事件”，不该关心“索引怎么追上来”

repo 只关心 DB 读写，不该决定并发顺序

你现在先确认模块归属的话：这是 infra 的投影/事件处理一致性策略，和业务用例层是分开的。这样你后面做 Outbox、重试、DLQ、幂等，也都能自然接上，不会把逻辑污染到 domain/usecase 里。