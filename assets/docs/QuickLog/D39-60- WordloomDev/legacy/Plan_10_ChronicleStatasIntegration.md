0. 总基准先钉死
你的新要求可以总结成三句：


简单：概念少、表少、页面少。


高度稳定：以后业务长大，旧数据 / 旧结构不打脸。


可拆：将来想砍掉 Bookshelf、改 Library 结构、重做报表，都不会把现在这块炸掉。


在这个前提下，我们重新规划 Chronicle / Stats。

1. Chronicle & Stats 要不要分？——结论：合并一个模块，只保留 Chronicle
你自己已经嗅到味道了：

Chronicle = 各种时长、数量、创建数……
Stats = 统一模块……
听起来像一回事？

是的，本质上它们都是在用同一批事件做两种呈现：


时间线样式 → “我什么时候干了什么”


汇总样式   → “最近整体长成什么样”


所以最稳妥的做法是：

域里只有一个模块：Chronicle（编年史）。
所有统计（Stats）只是 Chronicle 里的一个视图 / tab。

也就是说：


Workbox 菜单只保留：


Basement


Chronicle




进入 Chronicle 后再分两个 tab：


Timeline 时间线


Overview 概览（这就是原来的 Stats）




这样好处：


域模型少一个名词，你大脑也轻松；


数据只维护一套逻辑（事件流），不会出现“这边记一份、那边记一份”；


将来你想再把 Overview 搬出来单独做一个 Reports 页，也只是 UI 重组，不动后端。



2. 数据层：只做一件事——单表事件流 + 可选聚合表
为了长期最稳定，最经典的做法就是事件表 + 可选的日聚合。
2.1 核心：一张事件表 chronicle_events
字段可以简单到：
chronicle_events
- id
- occurred_at        // 时间
- actor              // 以后多用户可用，现在可以先填 'self'
- entity_type        // 'Library' | 'Bookshelf' | 'Book'
- entity_id          // 对应 id
- event_type         // 'BookCreated' | 'BookEdited' | 'MaturityChanged' | ...
- payload_json       // 可选：一些补充信息，json 存，后续好扩

这是唯一的真相来源（single source of truth）。
以后你要算什么：


某 Book 一共编辑过几次？


某 Bookshelf 最近 30 天活跃怎样？


某 Library 下有多少次 “Seed→Growing”？


全都由这个表算出来；
觉得慢了，再加缓存 / 日聚合表，不要一开始就堆一堆 counter 字段。
2.2 以后如果真的性能不够，再加一张“日聚合表”
比如：
daily_activity
- date
- entity_type
- entity_id
- edits_count
- created_count
- dwell_seconds
- maturity_up_count

这张表可以由 chronicle_events 批量生成，不影响设计纯度。
现在完全可以不建，把它当“将来要扩容时的外挂模块”。

3. Chronicle 模块：一套数据，两种视图
有了 chronicle_events 之后，Chronicle 模块可以分成两个视图：
3.1 Timeline 视图（Activity Log）
用途：回答 “最近发生了什么事？”


默认显示最近 7/30 天的事件列表：


时间


实体（Library / Bookshelf / Book 名称）


事件描述（“将 Book『StudyLog』从 Seed 标为 Growing”）




左侧提供过滤器：


时间范围


实体类型（只看 Book / 某个 Library）


事件类型（只看创建 / 只看成熟度变化）




你可以把它类比成 ESG / 合规里的“审计轨迹（audit log）”。
3.2 Overview 视图（Metrics Dashboard）
用途：回答 “整体状态和趋势怎么样？”
所有图表、数字都来自 chronicle_events 的查询或缓存。
先做最简单的三块就好：


活跃度（Activity）


最近 7/30 天，每天的 BookEdited 次数折线；


Top N 活跃的 Bookshelf / Book 列表。




成熟度（Maturity）


当前各状态 Book 数量：Seed / Growing / Stable / Legacy（条形或 donut）；


最近 30 天里 MaturityChanged 的次数趋势。




注意力债务（Staleness）


列出“长时间未编辑的 Growing/Seed Book”；


列出“Stable 但 90 天没打开”的 Book。




后面你想加 ESG 味更重的指标，也全部扩展在这个页面，不用再新开 Stats 模块。

4. 和 Library / Bookshelf / Book 的关系：只做“可选视图”，不绑死
为了将来的“拆卸自由”，一个重要原则是：

任何 Library / Bookshelf / Book 页面里出现的 Chronicle 信息，
都只是 “滤好的视图”，而不是新建责任中心。

实践上：


在 Library 详情页：


给一个小入口 “View chronicle for this Library”


点进去其实就是打开 Chronicle 页面 + 自动加过滤条件：


entity_type in ('Bookshelf', 'Book') AND library_id = xxx






在 Bookshelf / Book 页也是同理：只不过默认过滤更窄。


这样保证：


Chronicle 模块始终是一个独立的“工具箱视图”，


Library / Bookshelf / Book 聚合本身不需要知道 Chronicle 的太多细节；


以后你如果删掉 Bookshelf 这一层，只要保持 entity_type 的语义映射就行，Chronicle 表本身不用重构。



5. 行业成熟经验：为什么“事件流 + 视图分层”是长久解？
你问的第（3）点，往大了说就是：
成熟系统是怎么管 Activity / Metrics 的？
共性大概是三条：


底层统一“遥测管道”（telemetry）：事件流是一份


不管是日志（log）、统计（metrics）、trace，底层都是统一事件流；


不同产品只是在上面叠视图：


Activity Log


Dashboard / Insight


Alert / 报警




优点：不重复存逻辑，也方便以后做新的图表。




UI 上通常只分两个大块：Activity（时间线） + Reports / Insights（汇总）


很多 B2B SaaS 左侧菜单就是：


Activity / Audit log


Analytics / Reports




你现在做的是个人知识系统，完全可以缩成一个模块 + 两张 tab。




不要为指标去绑死 domain 结构


比如：如果你为了统计方便，硬在 Book 上加一堆 edit_count_last_7_days 之类字段，
将来 domain 结构一改，这些字段就会变成技术债。


比起“即算即存”的 counter，行业更倾向于 “事件 + 离线/缓存聚合”，
因为它对 future-proof 更友好。




你现在采用的“Chronicle 单模块 + 事件表 + 视图里做统计”，就是这条路线最简化版本。

6. 总结成一个非常短的实施指南


**域模块：**只保留一个 Chronicle，不再有单独的 Stats 域。


数据结构：


核心一张表：chronicle_events，记录 Library / Bookshelf / Book 的所有关键事件；


将来性能不够再加 daily_activity 作为外挂聚合表。




UI：


Workbox 下只有 Chronicle 菜单；


Chronicle 里两个 tab：

Timeline：事件流，支持过滤；

Overview：从事件流算出来的几个关键指标（活跃度 / 成熟度 / 注意力债务）。


与其他聚合的关系：

Library / Bookshelf / Book 只通过“过滤后的 Chronicle 视图”来看活动，不承担任何统计逻辑；

将来改 domain 层，只要保持事件流的 entity 信息不丢，就不会有大翻修。


这么设计，你现在这个“小软件”就已经有了简洁但工业级的“可观测性骨架”：
不挖坑、不堆概念、以后要扩 / 要拆，都不会卡住自己。
