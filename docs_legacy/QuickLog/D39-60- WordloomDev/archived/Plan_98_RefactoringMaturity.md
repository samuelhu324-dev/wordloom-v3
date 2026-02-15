一、问题复盘：为什么现在一改成熟度，全站就“抖”一下？

规则散落到处都是：
目前 maturity 相关逻辑分布在 book 模块的 domain service、use case、router 里，前端也有自己的 NextStepsChecklist 和进度条解释，一旦规则改动，很难确保所有地方同步更新。
耦合到 Book 聚合本身：
Book 实体里直接有 maturity_score、maturity、legacy_flag 等字段。
recalculate_book_maturity、update_book_maturity UseCase 直接操作 Book，并推送 Chronicle 事件。
一旦 service 里算法出错 / 依赖环境不对，读取 Book 时就可能报错（例如导入失败、依赖循环）。
“即算即写”模式放大了风险：
PATCH / 块增删 / TODO 变化立刻触发重算并写回 Book；
如果这个重算逻辑出异常，就会阻断本来可以成功的业务操作（比如只是改一句摘要）。
UI 也隐性依赖数值：
Book Overview 上的进度条、结构任务、按钮显隐都依赖 maturity_score；
前端对“40 分阈值”“70 分 Stable”等有自己的假设，一旦后端调整阈值却没同步，UI 语义就失真。
简化一句话：成熟度本质是一个“跨聚合视图”，但现在被当成 Book 的“内部字段”来用，导致边界渗透。

二、总体改造思路：把 Maturity 拨出来，做成独立模块

你给的目录很清晰：maturity 已经预留好了，现在要做的是：

Domain 层：定义“成熟度”的语言
把“Book 怎么成熟”这套规则，从 book module 抽出来放到 maturity.domain。
Application 层：对外只提供“查询 + 计算 + 审计”用例
不直接改 Book 表，只返回结果和建议。
需要改 Book 阶段时，走清晰的跨模块协作（例如通过事件总线）。
Infra 层：给 maturity 自己的 repository / model（可选轻量持久化）
可以存一些快照、规则版本、调分记录，而不是挤在 Book 表里。
API 层：成熟度模块自己的 routers
如 /maturity/books/{id}/snapshot、/maturity/books/{id}/recalculate。
book router 不再自己“懂规则”，只是调用 maturity 模块。
最终目标：调整成熟度算法 ≈ 只改一个模块 + 少量依赖，而不是牵动 Book/Chronicle/前端一大片。

三、从 Domain 开始划分：maturity 模块要定义什么？

建议在 backend/api/app/modules/maturity/domain/ 里，按 DDD 习惯先定义：

核心概念（Value Objects + Enum）

MaturityStage: 'seed' | 'growing' | 'stable' | 'legacy'
MaturityScore: 包含 value: int + version: str（规则版本号）
StructureTask:
id: 'title' | 'summary' | 'tags' | 'cover' | 'block_variety' | 'block_count' | 'todo_health' | ...
label: 人类可读标题
points: 这项能贡献多少分
completed: bool
MaturitySnapshot:
book_id
score: MaturityScore
stage: MaturityStage
tasks: list[StructureTask]
rule_version
calculated_at
纯算法服务：MaturityRuleEngine / MaturityService

输入：不再直接依赖 Book 实体，而是明确的只读 DTO：
BookProfile（title/summary/cover/tag_count/...）
BlockStats（block_count、block_type_count）
TodoStats（open_todo_count）
ChronicleStats（最近访问、阶段变更历史，可选）
输出：MaturitySnapshot
内部实现：
你现在的规则（标题+5，摘要+5，≥1 tag +5，≥3 block 类型 +5，封面+5，block 数 0–20 + 额外 0–20，TODO 0–20，ops bonus 0–60）全部藏在这里。
单独有 score_to_stage(score) -> MaturityStage。
领域策略：阶段是否允许变更

定一个 MaturityTransitionPolicy：
can_transition(current_stage, target_stage, snapshot) -> bool
里头放 Stable 需要≥70、TODO 为 0 等规则。
这块可以和现在 Book 的 state machine 对齐，但从 maturity 视角描述，而不是直接操作 Book。
这样做的效果是：

改评分规则 ≈ 只改 MaturityRuleEngine；
改阶段门槛 ≈ 只改 MaturityTransitionPolicy；
Book / Chronicle / Block / Tag 统统只是“输入数据来源”。
四、Application 层：maturity 有哪些用例？

在 backend/api/app/modules/maturity/application/ 里，可以设计一些独立用例：

CalculateBookMaturityUseCase

输入：book_id + 可选 override（tag_count / block_count / open_todo_count / operations_bonus 等）。
步骤：
调用 book_repo / block_repo / todo_snapshot_repo / chronicle_repo（通过 ports 注入）拿到所需快照；
调用 Domain 里的 MaturityRuleEngine 得到 MaturitySnapshot；
（可选）将 snapshot 写到 maturity 自己的表；
返回给调用者。
不负责改 Book 表，只算结果。
ReconcileBookMaturityStageUseCase

输入：book_id。
步骤：
通过 CalculateBookMaturityUseCase 得到 snapshot；
用 MaturityTransitionPolicy 判断是否需要从 SEED→GROWING / GROWING→STABLE 等；
如果需要变更：
触发一个 领域事件：BookMaturityStageSuggested(book_id, from_stage, to_stage, score, rule_version)；
或者显式调用 Book 模块的 UpdateBookMaturityUseCase（通过 port），由对方真正改聚合并写 Chronicle；
返回“是否建议变更、建议目标阶段”。
ListBookMaturityHistoryUseCase（可选）

如果你想给 maturity 自己的 repository 存历史快照，这里可以支持按时间段查询，以后用于统计。
关键点：所有这些 UseCase 都在 maturity module 里，对外暴露的是“只读 + 建议”，真正修改 Book 的操作仍然由 book 模块掌控。

五、Infra：为 maturity 新增 repository & models

你截图里已经有：

book_repository_impl.py
book_models.py
现在 maturity 也可以有一套轻量 infra：

数据库模型：maturity_models.py

放在 backend/infra/database/models/maturity_models.py：
MaturitySnapshotModel
id
book_id (FK)
score
stage
rule_version
components_json（存各 StructureTask / ScoreComponent；JSON/BLOB）
calculated_at
MaturityRuleVersionModel（可选）
当前使用中的规则版本号、描述、启用时间。
这样你未来改规则时，可以知道“在 v1.0 规则下，它曾经是 65 分”。
Storage 层 Repository：maturity_repository_impl.py

放在 backend/infra/storage/maturity_repository_impl.py：
SQLAlchemyMaturityRepository 实现：
save_snapshot(snapshot: MaturitySnapshot);
get_latest_by_book(book_id);
list_history(book_id, limit, offset);
在 __init__.py 或容器里注册。
API app 层的 Output Port

在 output.py 定义：
MaturitySnapshotRepository 抽象接口；
dependencies_real.py 里把它绑定到 SQLAlchemyMaturityRepository。
好处：

以后你做“成熟度趋势图 / 审计报告”有天然数据源；
Book 表可以逐步减负（长期可以考虑把 maturity_score 留作“最近一次 score 缓存”，而真正的可信计算都走 maturity 模块）。
六、API / Router：给 maturity 模块自己的 HTTP 入口

在 backend/api/app/modules/maturity/routers/maturity_router.py 里，可以设计：

GET /maturity/books/{book_id}/snapshot
返回：当前计算的 snapshot（实时算 + 可选读取最近快照）。
POST /maturity/books/{book_id}/recalculate
Body 可选传 override（tag_count / block_count / open_todo_count / operations_bonus / cover_icon），调用 CalculateBookMaturityUseCase。
POST /maturity/books/{book_id}/reconcile-stage
用于后台批量作业：算完后，如果需要改阶段，只返回“建议”，由任务或运维脚本再决定是否应用。
同时：

book_router 可以保留一个简单 Proxy：
比如当前的 /books/{id}/maturity/recalculate，内部改为调用 maturity 模块 UseCase，而不是直接自己算，避免重复规则。
前端改到直接打 /api/v1/maturity/books/{id}/snapshot 也可以，逐步去掉对 Book 的隐性耦合。
七、RULES 分层：三份规则文件怎么写 maturity 部分

你给了 DDD_RULES.yaml / HEXAGONAL_RULES.yaml / VISUAL_RULES.yaml，成熟度模块应该这样落地：

DDD_RULES.yaml

在 Book Domain 区下新增一个大段：
POLICY-BOOK-MATURITY-MODULE-V1：
明确：成熟度领域逻辑迁移到独立模块 maturity；
Book 只持有：maturity_stage（枚举） + legacy_flag（分区标记）；
maturity_score 字段仅作为“最近快照”，不参与领域决策，决策应以 maturity 模块计算结果为准。
记录：
评分规则（现在这版 Plan_97 的 0–100 细则）；
阶段映射（Seed/Growing/Stable/Legacy 阈值）；
与 Chronicle 的关系（阶段变更事件从 Book 发出，但触发条件来自 maturity 模块的建议）。
HEXAGONAL_RULES.yaml

新增 module_maturity: 段：
说明：
Domain：MaturityRuleEngine + MaturityTransitionPolicy；
Application：CalculateBookMaturityUseCase / ReconcileBookMaturityStageUseCase；
Ports：
Input Ports：上面两个 use case；
Output Ports：BookReadModelPort（只读）、BlockStatsPort、TodoStatsPort、ChronicleReadPort、MaturitySnapshotRepository。
Adapters：
Infra：SQLAlchemyMaturityRepository；
Integration：通过 dependencies_real.py 注入 Book / Block / Chronicle 仓储。
明确 hexagonal 规则：
maturity不得直接 import book.domain.book.Book，只能通过 port 取得只读 DTO；
不能在 maturity 内直接发 HTTP 请求或访问外层框架。
VISUAL_RULES.yaml

在 book_maturity_visual_rules 下补一条：
概览页面的进度条、结构任务、按钮显隐，必须仅依赖：
GET /maturity/books/{id}/snapshot 的结果，而不是自行推断；
当 maturity 模块降级 / 不可用时：
UI 回退为“阶段标签 + 简单提示”，不阻断 Book 编辑。
八、ADR-113：这次“抽模块”要记录什么？

你截图里 ADR 目录已有 ADR-111 等；ADR-113-book-maturity-module-extraction.md 应该写清楚：

Context
之前 maturity 规则耦合在 book 模块，引发的典型问题：
改算法导致 Book API 失败；
前后端规则不一致；
难以实验不同规则版本。
Decision
引入独立 maturity 模块：
Domain/Application/Router/Infra 全套；
Book 只保留阶段与 Legacy 等硬状态字段；
评分规则和结构任务定义集中在 MaturityRuleEngine。
Consequences
正面：
可以安全迭代评分规则，不影响 Book 核心 CRUD；
有成熟度历史快照，方便做报表与调参；
与 Chronicle 的边界更清晰：阶段变更事件只由 Book 聚合发出，但触发条件统一来源于 maturity 模块。
负面 / 代价：
多了一层间接：任何需要分数的地方都要多打一跳 API；
短期需要迁移现有 recalculate_book_maturity / update_book_maturity UseCase；
部分测试要重新调整到新的 module。
九、行业+Wordloom 综合观点：这套拆分“值不值”？

行业经验

复杂 SaaS（Notion / Linear / Jira）里，“健康度 / 评分 / 审计”几乎都是独立子系统：
业务聚合保留简单状态（Active / Done / Archived）；
打分、推荐、提醒在“Insights / Analytics / Suggestions”模块实现。
原因：
算法要被频繁调整甚至 A/B 测试；
有概率会引入 ML / 统计，和事务写路由必须解耦；
“错了可以回滚 / 忽略”，不能影响主交易链路。
对 Wordloom 的好处

你现在就有 Plan_91/96/97、RULES、ADR 这样的设计文档，说明这个项目未来一定会继续演进，成熟度肯定不是一次定型；
把 maturity 当成独立模块，能支持：
分环境运行不同“评分策略”（比如自己测试版 vs 正式版）；
做“成熟度实验室”：快速迭代结构任务、权重与 UI 展示，而不用担心把 Book 写挂。
短期建议

第一步只做“计算模块化”，暂不大改表结构：
先把现有 BookMaturityScoreService / recalculate_book_maturity 搬到 maturity module，但对外接口形态保持兼容；
Book 表里的 maturity_score 先继续当缓存；
渐进地让所有“需要算分的地方”都通过 maturity module，这时你已经完成 80% 解耦。
第二步再考虑持久化与历史：
等需求确实要“查看历史分布 / 曲线”时，再加 maturity_models 表；
同时审视是否要从 Book 表去掉某些字段。
十、简短结论

现在的瘫痪问题，本质就是“成熟度 = 聚合视图，却被当成 Book 内部字段”，边界渗透导致系统脆弱。
把 maturity 拨成独立模块（domain + application + infra + router），并在 RULES + ADR-113 里明确规则，是一个非常符合 DDD/Hexagonal 的方向。
一旦完成这次抽离，你以后：
改权重 / 改阶段阈值 → 改一处；
做不同规则版本 → 在 maturity 表里多一列 rule_version；
想完全关掉成熟度 → 只要停止 maturity 服务，Book CRUD 仍然正常工作。
如果你愿意，我下一步可以按这个设计实际在 modules/maturity 下帮你生成骨架代码（domain/service/ports/repository stub）和一版 ADR-113 草稿，你再根据实际运行情况细调。