Plan Overview
目标：依据 Plan14 将 Book 页面重构为“成熟度分层”视图（Seed/Growing/Stable/Legacy），把成熟度作为 Book 聚合内原生字段与枚举；前后端与三份规则文件 (DDD / HEXAGONAL / VISUAL) 完全对齐，并新增 ADR-092 记录决策与迁移策略。

一、概念与契约梳理
新增领域枚举：BookMaturity = SEED | GROWING | STABLE | LEGACY（Domain 用 UPPER_SNAKE；传输层 lower_case）。
成熟度含义：
SEED：刚创建/零散草稿；可编辑全部基础元数据；无封面图。
GROWING：结构成形、正在整理；允许统计 block_count / recent_edit_count；仍不可设封面。
STABLE：整理完成；可设封面（cover_media_id 或 URL Phase A）；行样式紧凑。
LEGACY：历史归档；只读（除恢复操作）；不参与“完成度进度”分子。
进度指标：stable_count / (total - legacy_count) 用进度条与数值展示。
迁移策略：初始所有旧 Book 迁移为 SEED（或按已有 block_count≥阈值回填为 GROWING）；默认创建为 SEED。
二、后端改动步骤
数据库迁移：ALTER TABLE books ADD COLUMN maturity VARCHAR(16) NOT NULL DEFAULT 'seed'; + 索引 idx_books_maturity.
Domain 层：添加枚举 BookMaturity(Enum)；在 Book.create() 默认 SEED；方法 mark_growing(), mark_stable(), mark_legacy(), restore_from_legacy().
业务规则：
只能从 SEED → GROWING → STABLE；STABLE → LEGACY；LEGACY → (恢复) STABLE 或 GROWING（选择 STABLE，若需要回退允许 GROWING）。
封面设置 UseCase 校验：仅 STABLE 可调用。
Repository/DTO：序列化 maturity → lower_case；过滤/排序不自动按 maturity 分段（UI 分层保持 Hexagonal 边界）。
API：GET /books 增加 maturity；PATCH /books/{id}/maturity 轻量变更端点（或复用通用更新端点）。
测试：单元测试迁移 + 变更方法状态机；端到端验证列表返回四种 maturity 分布与排序不破坏现有分页。
三、前端适配步骤
更新 BookDto / adapter：新增 maturity: 'seed' | 'growing' | 'stable' | 'legacy'.
分层逻辑：在 BookMainWidget 中将分页返回的 items 按 maturity 分成四个数组；计算 summary。
组件结构：
SummaryBar：显示四类数量 + 完成度进度条。
Section 容器：Seed / Growing / Stable / Legacy（空状态定制文案）。
样式与视觉（对应 VISUAL_RULES 新条目）：
Seed 行：背景纯白或极浅灰，icon 半透明线框，允许备注行。
Growing：淡主题色块背景，显示 block_count / 7 日编辑次数。
Stable：紧凑行 + 封面 thumb + 绿色 badge。
Legacy：淡灰 + 次要文本色。
动画：跨区移动时淡入 + slide（100–150ms）；Stable 初次转换闪一次轻高亮。
交互：
批量选择（可选 Phase B）；单行右侧成熟度变更菜单。
Stable 封面按钮 hover 出现；非 Stable 时禁用（tooltip 解释）。
本地状态：maturity 不缓存为 UI 状态；分页参数与现有 listBooks 保持。
统计：完成度进度条实时基于前端当前页的聚合；如需全量准确度，后端可选新增聚合端点（暂不做）。
四、三份 RULES 更新要点
DDD_RULES.yaml：
新增 CONVENTION-ENUM-BOOK-MATURITY（适配到现有 CONVENTION-ENUMS-001）具体列出四值。
新增 POLICY-BOOK-MATURITY-STATE-MACHINE（允许的转换列表 + 只读限制）。
更新 POLICY-BOOK-LISTING：声明 UI 分层基于 maturity，不改变端点形式；分页仍 V2 契约。
更新任何旧描述中“仅 tags 过滤”的段落，补上 maturity 分层语义。
HEXAGONAL_RULES.yaml：
新增 book_maturity_strategy：决策点（UI 分段、Domain 状态机、Adapter lower_case）。
标注“封面设置端口”受 maturity=stable 限制；不创建新 Repository 方法（仅验证 + 更新）。
Pagination V2 已存在 → 增加 maturity 字段传输说明与不在 Domain 存储派生进度。
VISUAL_RULES.yaml：
新增 RULE_BOOK_MATURITY_SEGMENTS（四区视觉、动画、空状态文案、进度条公式）。
新增 RULE_BOOK_STABLE_COVER_CONTROL（Stable 显式封面按钮 / 非 Stable 禁用）。
更新旧的 book_preview_cards_phase_2 说明：补“成熟度视觉套件已激活”。
空状态文本策略 Seed / Stable / 全空。
五、ADR-092 编写结构
文件：assets/docs/ADR/ADR-092-book-maturity-segmentation-and-ui-overhaul.md
章节：

Context（现状缺少组织感 → Plan14 目标 / 荒芜→井然叙事）
Decision（枚举加入 Domain；UI 分层；Stable 封面限制；分页保持 V2）
Consequences（优点/风险：迁移默认 SEED、额外状态机复杂度、未来统计端点扩展）
Implementation Notes（迁移脚本 / 枚举转换 / 前端组件路径 / 新空状态文案）
Rollout（步骤、批量回填策略、回退：删除列并回退前端 grouping）
Future Work（批量操作、成熟度自动提升策略、Chronicle 集成、聚合统计端点）
六、迁移与回滚计划
Phase 0：添加列 + 后端 DTO + 前端接受字段但仍用单列表（隐藏分段功能开关）。
Phase 1：启用 UI 分段 + SummaryBar；写入状态机方法。
Phase 2：Stable 封面按钮启用；Legacy 只读行为 enforced。
回滚策略：若出现不稳定，前端降级隐藏分段（feature flag），后端保留列不删除；严重问题可 ALTER TABLE DROP COLUMN maturity 并移除枚举。
七、测试与质量保障（概述）
单元：状态转换方法 + 封面权限校验。
集成：ListBooks 返回包含 maturity 四值；分页维持正确 has_more。
前端：分段渲染快照 + 动画存在性 + 禁用封面按钮（非 Stable）。
数据迁移验证：随机抽样 50 条创建记录默认 SEED。
八、工作分解（建议顺序）
后端：枚举 + 列迁移 + Domain/service 方法 + DTO 输出。
Adapter：更新 list/create/update 端点序列化 + tests。
前端类型与 adapter 更新。
UI 分段组件 + SummaryBar。
视觉与动画 + 空状态。
Stable 封面权限逻辑。
批量操作（可后置）。
更新三份 RULES。
编写 ADR-092。
验证与回归测试。
九、需确认的开放问题（供你裁剪）
初始回填策略：全部 SEED vs. 基于 block_count >= N 标记 GROWING？推荐阈值 N=5。
Legacy 恢复目标：直接 STABLE 还是回到 GROWING？（当前计划选 STABLE，可调整）。
进度条分母：是否排除 Legacy（当前排除）？
统计聚合：是否需要后端快速聚合端点避免大页扫描（暂不做）。
请审阅以上计划，反馈你的裁剪/调整需求；确认后我再进入 agent 模式执行。需要对某一部分做更细拆分或加英文对照，告诉我即可。