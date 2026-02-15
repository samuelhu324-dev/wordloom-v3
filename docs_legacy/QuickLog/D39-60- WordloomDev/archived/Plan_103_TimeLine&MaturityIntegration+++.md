Plan: Plan102 时间线 & 成熟度一体化改造（规划版）
围绕 Plan102，只动 Maturity 模块 + Chronicle/Timeline 模块，并保持系统当前可用（能正常打开书页）。

Steps
梳理现状 & 截图对应
1.1 对照 Plan_102_TimeLine&MaturityIntegration++.md，通读现有后端 maturity / chronicle 代码与前端书籍概览/时间线页面，标出与设计差异（例如：成熟度是否仍由 Book 字段驱动、最近事件来源是否统一）。
1.2 明确“截图1：概览卡片 + 结构任务卡片”、“截图2：时间线Tab”、“截图3：ADR 目录位置”的实际文件路径，记录需要修改的组件与 API。

后端 Domain 对齐：Maturity 纯函数与结构任务
2.1 在 domain 中新增/完善：
- calculate_maturity(snapshot_input)：实现 Plan102 中的结构得分规则（标题/摘要/blocks/todos/tags/visits），返回 { score, stage, contributions[] }。
- resolve_structure_tasks(snapshot)：基于 BookMaturitySnapshot 和静态 ALL_TASKS 配置，计算 StructureTaskState[]（locked/pending/completed/regressed）。
2.2 定义并实现 BookMaturitySnapshot、Contribution、StructureTask、StructureTaskState 等纯 Domain 类型，确保与 Plan102 的字段一一对应（blocksCount、todosCount、visits90d、hasTitle、hasSummary、tagsCount、snapshotAt 等）。
2.3 在现有 MaturitySnapshotSchema / repository 层中，增加/映射 TaskState 序列化结构，让前端可以一次性拿到 score + stage + tasks。

后端 API：Recompute & Recent Events 封装
3.1 在 maturity_router.py 中：
- 新增 POST /maturity/books/{book_id}/recompute：
- 从数据库统计 snapshotInput（blocksCount / todosCount / visits90d / summaryLength / tagsCount / hasTitle / hasSummary 等）。
- 通过 domain 层调用 calculate_maturity + resolve_structure_tasks。
- 写入或更新 maturity_snapshots 表记录，并返回最新的 snapshot + tasks。
3.2 在 chronicle：
- 扩展/确认 Book 事件类型集合，覆盖 Plan102 中的 BookEventKind（包含 structure_task_completed / regressed / maturity_recomputed / maturity_stage_changed 等）。
- 统一封装写事件的 helper（例如 record_book_event(kind, payload)），在 recompute 逻辑里根据 score、stage、task 状态变化写：
- maturity_recomputed（oldScore → newScore）
- 如有阶段变化写 maturity_stage_changed；
- StructureTask 完成/回退分别写 structure_task_completed / structure_task_regressed。
3.3 新增 GET /chronicle/books/{book_id}/recent-events：
- 按 Plan102 的“强事件”集合过滤（created / summary_added_removed / maturity_stage_changed / structure_task_*），按时间倒序限制 N 条。
- 返回简洁 DTO（id / occurred_at / kind / payload）。

前端：概览页与 Timeline Tab 对齐 Plan102
4.1 概览页顶层指标条（STAGE / SCORE / SNAPSHOT / BLOCKS / EVENTS…）：
- 修改 page.tsx 中 overview 计算逻辑，完全依赖 maturity snapshot 中的 score/stage/createdAt 及 counts，而不是任何 Book 旧字段。
4.2 「结构任务」卡片：
- 将现有 NextStepsChecklist 改造为消费 maturity API 返回的 StructureTaskState[]：
- 优先展示当前阶段下 3~5 个 pending 任务；
- completed 折叠计数显示；
- locked / regressed 用淡化样式或 tooltip 表达。
- 「刷新成熟度快照」按钮：
- 调用 POST /maturity/books/{id}/recompute，并在成功后并行刷新：
- 最新 maturity snapshot；
- recent events；
- 概览统计卡片。
4.3 Timeline Tab：
- 使用 GET /chronicle/books/{book_id}/recent-events 填充概览页“最近事件”卡片（只显示强事件）；
- Timeline Tab 使用 Chronicle 全量事件列表（已有 hook / endpoint 可适配），并在渲染时针对 Plan102 中的关键事件 kind 显示更友好的说明（例如 maturity_stage_changed、structure_task_completed）。

RULES 三文件对齐 Plan102（DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES）
5.1 打开 DDD_RULES.yaml：
- 找出有关 Book、Maturity、Chronicle 的旧规则条目，按 Plan102 更新：
- 明确 Maturity 与 Chronicle 各自的聚合与职责（score 与 snapshot 属于 Maturity，事件与审计属 Chronicle）。
- 补充结构任务与 snapshot、事件之间的关系描述。
5.2 打开 HEXAGONAL_RULES.yaml：
- 校正与新增：
- 确认 Maturity 纯 Domain 在 UseCase 层作为服务被调用，Repository 只负责 snapshot 持久化。
- Chronicle Repository 负责事件持久化与过滤（recent vs full timeline）。
5.3 打开 VISUAL_RULES.yaml：
- 更新关于 Book 概览页的 visual 规则：
- 顶部指标条由 snapshot 驱动；
- 下方两个卡片分别绑定 recent-events 与结构任务 snapshot；
- 明确“刷新成熟度快照”按钮位置与行为（不涉及 theme 细节，只写交互与布局关系）。

ADR-114 撰写与最近改动归档
6.1 在 ADR 下新建或更新 ADR-114-*.md（命名仿照现有 ADR-111~113 样式）：
- Sections 建议：Context、Decision、Consequences、Implementation Notes。
- 把 Plan100 + Plan102 带来的最新 Decisions 归纳进去：
- Maturity 与 Chronicle 职责边界；
- 使用 snapshot + structure tasks + events 形成闭环；
- 前端 Book 概览与 TimeLine Tab 的新数据流。
6.2 在 ADR 中引用：
- DDD/HEXAGONAL/VISUAL 三个 RULES 文件的对应条目（简要编号即可）；
- 关键 API（/maturity/books/{id}/recompute, /chronicle/books/{id}/recent-events）与主要 DTO 字段。
6.3 标注迁移状态：
- “现有 Book 旧字段仍保留，仅作为兼容层；所有新 UI 已迁移至 maturity snapshot + chronicle events”；
- “未来计划：在全部书籍完成第一次 recompute 之后，逐步废弃旧字段与逻辑”。

验证与回归检查（保证可以重新打开软件查看内容）
7.1 后端：
- 本地或 WSL2 中启动 uvicorn，确认不再有 SyntaxError / IndentationError，核心路由 /maturity、/chronicle、/books 正常返回。
- 针对 recompute 与 recent-events 写或更新最小集成测试（可放在现有 backend tests 目录中），至少覆盖：
- 首次 recompute；
- 结构任务完成/回退时事件的写入。
7.2 前端：
- 启动 dev server，打开 Book 详情页：
- 顶部指标条显示来自 snapshot 的分数与阶段；
- “最近事件”卡片有内容且与手动 recompute 触发的事件对应；
- “结构任务”卡片显示合理 checklist，点击“刷新成熟度快照”后数据刷新且无报错。
7.3 文档：
- 交叉检查 Plan102、三份 RULES、ADR-114，确保描述一致，没有互相矛盾的旧内容残留（尤其是旧的“同步实时重算”表述）。

Further Considerations
事件表历史数据：是否需要为已有事件补一层 migration 或兼容 mapper（例如老的 maturity 相关事件 kind 映射到新的枚举）。
自动触发策略：是否在用户访问 Book 或每日定时自动触发一次 recompute，而不是完全依赖手动按钮（可以在 ADR 中留作 Future Work）。

////////////////////////////////////////////////////////////////

Plan: 按 Plan102 落地时间线 & 成熟度一体化（执行版）
下面这份是给后续“agent 模式”直接执行的详细任务清单，只围绕 Maturity + Chronicle/Timeline，不动主题和配色。

Steps
梳理现状，对齐 Plan102 设计
1.1 阅读 Plan_102_TimeLine&MaturityIntegration++.md 全文，提取核心数据结构与规则（BookMaturitySnapshot、BookEvent、阶段分界、结构任务模型与状态机）。
1.2 在后端浏览 maturity 与 chronicle，记录当前与 Plan102 差异：
snapshot 里已有/缺失的字段（blocksCount、todosCount、visits90d、hasTitle 等）。
Chronicle 事件枚举与存储结构是否覆盖 Plan102 的事件种类。
1.3 在前端确认涉及页面与组件：
概览页：page.tsx（顶部指标条 + 最近事件卡片 + 结构任务卡片）。
相关组件：NextStepsChecklist、时间线组件、maturity hooks。
确认当前是否全部走 /maturity 与 /chronicle API。
后端 Domain：实现/补全 Maturity 纯函数与结构任务
2.1 在 domain 中新增/完善：
calculate_maturity(snapshot_input)：
入参包含 Plan102 中列出的结构字段（blocksCount、todosCount、visits90d、summaryLength、tagsCount、hasTitle、hasSummary）。
实现阶段分界：0–29 seed / 30–59 growing / 60–89 stable / 90–100 legacy。
实现基础得分规则（标题/摘要/blocks/todo/标签/访问）的逐条 Contribution 计算，并返回 { score, stage, contributions[] }。
resolve_structure_tasks(snapshot)：
定义 StructureTaskId 与 StructureTask，按 Plan102 的 ALL_TASKS 建一个静态配置表。
定义 StructureTaskState { task, status }，根据 snapshot 的布尔条件与计数字段判定 locked | pending | completed | regressed。
2.2 定义/补充 Domain 类型：
BookMaturitySnapshot（Python dataclass 或 Pydantic model，仅在 Domain 层使用），字段映射 Plan102 的接口，包括 snapshotAt（对应 created_at）、lastEventAt、flags 等。
确认 snapshot 与数据库表 maturity_snapshots 的映射关系，必要时在 repository 层增加读写 tasks / components 的序列化逻辑。
2.3 修改 MaturitySnapshotSchema 与相关 assembler：
从 Domain snapshot + taskStates 构造当前前端已经使用的 DTO（BackendMaturitySnapshot 结构：score.value / score.components / tasks[] / stage / manualOverride 等）。
确保不丢失已有字段（例如 manual_override、manual_reason）并兼容新任务结构。
后端 API：Recompute & Recent Events
3.1 在 maturity_router 中新增重算接口：
POST /maturity/books/{book_id}/recompute：
从 DB 聚合当前书的统计数据：blocks 总数、todo 列表数、最近 90 天访问数、最后访问时间、最后事件时间、摘要长度、标签数量、标题/摘要/封面图是否存在等。
调用 calculate_maturity 得到 { score, stage, contributions }；
构造 BookMaturitySnapshot 并调用 resolve_structure_tasks(snapshot) 得到 TaskState 列表；
将 snapshot + score + components + tasks 写入/更新 maturity_snapshots 表，记录 created_at（即 snapshotAt）。
返回最新 snapshot DTO（前端已期望的格式）。
3.2 在 Chronicle 模块中统一事件写入：
扩展事件类型定义，覆盖 Plan102 需要的所有 BookEventKind（至少含 maturity_recomputed、maturity_stage_changed、structure_task_completed、structure_task_regressed）。
提供 helper：record_book_event(book_id, kind, payload)，供 recompute 用。
在 recompute 流程中：
比较旧 snapshot 与新 snapshot：
如 score 或 stage 改变 → 写一条 maturity_recomputed（包含旧/新分数）和可选 maturity_stage_changed（从/到阶段）。
检查任务状态变更：pending→completed 记 structure_task_completed（带 taskId 与分数），completed→regressed 记 structure_task_regressed。
3.3 新增 “最近事件” API：
在 Chronicle router 中实现 GET /chronicle/books/{book_id}/recent-events?limit=N：
从事件表中过滤 Plan102 中的“强事件”：created、summary_added/removed、maturity_stage_changed、structure_task_completed/regressed。
按 occurred_at 倒序，限制 N 条（例如默认 5 条）。
返回简洁 DTO：id, occurred_at, kind, payload。
前端：概览页 / 时间线 Tab 对应改造
4.1 更新 Book 概览顶部指标条：
在 BookDetailPage 中：
确认 useLatestBookMaturitySnapshot 已经提供 score/stage/createdAt；
调整 overview 统计逻辑：
STAGE 只读 maturity snapshot 的 stage；
SCORE 使用 snapshot.score.value；
SNAPSHOT 使用 snapshot.createdAt（相对时间 + tooltip 实际时间）；
BLOCKS / EVENTS / VISITS 等数值可从 snapshot 或额外 API 补全，但不再使用旧 book.maturity* 字段。
4.2 “最近事件”卡片：
新增或更新前端 API：GET /chronicle/books/{id}/recent-events 对应的 client + hook（放在 features/chronicle 下）。
概览页中“最近事件”卡片改为调用该 hook：
渲染最近 N 条强事件，格式为：相对时间 + 图标/emoji + 一句 summary（根据 kind + payload 拼出中文文案，如“成熟度升级为 Growing”、“完成结构任务『写摘要』”）。
保留右上角“查看全部”按钮，切换到 Timeline Tab。
4.3 “结构任务”卡片：
调整 NextStepsChecklist：
不再基于 BookDto 内字段推导任务，而是消费 maturity snapshot DTO 中的 tasks 或 TaskState；
只展示当前阶段下若干 pending 任务（例如 3~5 个），其余状态以折叠/计数方式展示。
更新概览页中对 NextStepsChecklist 的调用：
传入最新 snapshot（或者 snapshot.tasks + snapshot.stage），去掉对 book 上旧成熟度字段的依赖。
在卡片右上角放置 “刷新成熟度快照” 按钮：
点击 → 调 POST /maturity/books/{id}/recompute；
成功后并行 refetch：
useLatestBookMaturitySnapshot；
useRecentChronicleEvents（新 recent-events hook）；
任何依赖 snapshot 的 overview 统计。
RULES 三文件的同步修订
5.1 DDD_RULES.yaml：
在 Book / Maturity / Chronicle 相关章节中：
明确：
Maturity 负责 score / stage / snapshot / structure tasks；
Chronicle 负责记录 BookEvent、包括 maturity 相关事件与任务完成/回退事件；
移除或标记过时的“实时同步计算分数”描述，改为“按需/定期 recompute”。
5.2 HEXAGONAL_RULES.yaml：
更新 UseCase 与 Adapter 关系：
Book 写操作仅负责 Domain 行为及 DB 变更，不直接“算分”；
Maturity 作为独立 Domain 服务，通过 UseCase（例如 RecomputeBookMaturityUseCase）被触发；
Chronicle 作为独立持久化适配器，供 UseCase 写入事件与查询 timeline / 最近事件。
5.3 VISUAL_RULES.yaml：
更新 Book 详情页规则：
第一行指标条由 maturity snapshot 驱动；
第二行两个卡片固定为“最近事件 Chronicle”和“结构任务（基于成熟度计分）”；
按 Plan102 说明的行为简要写出交互（例如刷新按钮行为），不涉及具体颜色/主题。
新增 ADR-114：TimeLine & Maturity Integration v2
6.1 在 ADR 目录创建 ADR-114-timeline-and-maturity-integration-v2.md（命名仿照 ADR-111+ 系列）：
Context：
简述旧方案问题（Book 字段耦合、分数更新不可追溯、结构任务由前端推导等）。
引用 Plan100 / Plan102 作为设计背景。
Decision：
Maturity 与 Chronicle 的职责边界；
使用 snapshot + structure tasks + events 的闭环设计；
提供 recompute / recent-events 两个关键 API。
Consequences：
优点：可追溯、易调权重、与 UI 解耦；
成本：需要维护 snapshot 表和事件流的一致性。
Implementation Notes：
简述 Domain 模块、API 端点、前端页面的主要结构；
标明与 DDD/HEXAGONAL/VISUAL RULES 中条目的对应关系。
6.2 把最近几轮改造（maturity 模块抽离、snapshot 表、前端概览重构）的关键点整理进 ADR-114，而不是散落在 QuickLog 中。
基本验证与回归（确保能正常打开书页）
7.1 后端：
运行后端测试或至少针对 maturity / chronicle 的关键路径写 1–2 个集成测试（recompute + recent-events），确认：
接口 2xx 响应，返回内容字段完整；
调用 recompute 后，事件表中存在合适种类的 BookEvent。
7.2 前端：
启动 dev server，打开任意 Book 详情页：
概览指标条正确显示当前阶段与分数；
“最近事件”卡片展示近几次重要操作；
“结构任务”卡片显示合理 checklist，点击“刷新成熟度快照”后 UI 数据能更新，无前端错误。
7.3 文档：
简单自检：
Plan102、DDD_RULES、HEXAGONAL_RULES、VISUAL_RULES、ADR-114 在术语与职责划分上无明显矛盾；
对旧行为有保留说明或标记为 deprecated（必要时）。
如果这些步骤 OK，你可以直接切到 agent 模式，从 Step 2 开始逐项实现和修订。