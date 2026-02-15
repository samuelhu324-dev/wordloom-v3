# ADR-120: Plan111 Book Maturity Score Alignment

- Status: Accepted (Nov 30, 2025)
- Deciders: Wordloom Core Team
- Context: ADR-092 (Book maturity segmentation), ADR-111 (Maturity + timeline integration), ADR-117 (Combined view/search), ADR-118 (Resilient shell), ADR-119 (Summary parity)
- Related Artifacts: `backend/api/app/modules/book/domain/services/plan111.py`, `backend/api/app/modules/book/domain/services/maturity_score.py`, `backend/api/app/modules/maturity/application/use_cases.py`, `frontend/src/features/maturity/model/api.ts`, `frontend/src/features/maturity/ui/MaturityScoreBreakdown.tsx`, `assets/docs/DDD_RULES.yaml`, `assets/docs/HEXAGONAL_RULES.yaml`, `assets/docs/VISUAL_RULES.yaml`

## Problem / 背景

1. **Plan102 梯度无法解释真实成熟度。** 旧模块使用“基础加点 + Block 线性曲线 + TODO 惩罚”的混合模型，无法回答“结构完整度”“活动性”“质量深度”分别贡献多少分，Product/运营也无法对症下药。
2. **Structure Task 缺乏统一蓝图。** 各端口维护的 TODO/任务列表内容与词汇不一，`reasons[]` 与任务状态没有共享语义，导致 Bookshelf 视图与 Overview 面板出现认知分裂。
3. **文档与 UI 合同缺口。** RULES 文件仍描述 Plan102 时代的指标（例如 reasons[]、block_count_curve），前端 tooltip 依赖的字段名称也与后端返回不一致，提升/扣分无法追溯。
4. **人工加成缺乏安全阈值。** 运营在数据修复时需要手动 ±40 分，常常跳过真实状态，无法区分“结构完整但暂未活跃”和“活动良好但结构未完成”。

## Decision / 决策

1. **启用 Plan111 四象限评分。**
   - 结构（0-30）：标题、摘要长度、标签、封面图标、Block 阶梯。
   - 活动（0-30）：最近编辑/访问频次/TODO 健康度。
   - 质量（0-20）：Block 类型多样性 + 结构深度（Block × 摘要组合）。
   - 结构任务（0-20）：long_summary、tag_landscape、outline_depth、todo_zero 以 blueprint 统一维护。
   - 人工调整收敛到 ±5 分，factor 固定为 `manual_adjustment`。
2. **集中封装 `plan111.py`.** 新增 `Plan111SnapshotInput`、`Plan111ScoreComponent`、`Plan111StructureTaskBlueprint`、`calculate_plan111_score` 与 `is_plan111_task_completed`，供 `BookMaturityScoreService` 与 `CalculateBookMaturityUseCase` 复用，确保前后端共享同一梯度。
3. **应用层全面接入。** `BookMaturityScoreService`、`maturity/application/use_cases.py` 通过 snapshot builder 生成 Plan111 数据，stage 推导仍复用 `derive_maturity_from_score`，任务列表根据 blueprint 与当前阶段计算 LOCKED/PENDING/COMPLETED/REGRESSED。
4. **前端/协议同步。** `frontend/src/features/maturity/model/api.ts` 转向消费 `score.components[]`，`MaturityScoreBreakdown` 组件按 factor 前缀（structure/activity/quality/task/manual）渲染；UI tooltip 不再重算，仅展示后端 detail。
5. **RULES 文档更新。** DDD_RULES `POLICY-BOOK-MATURITY-*`、HEXAGONAL_RULES `book_maturity` 小节、VISUAL_RULES `book_maturity_visual_rules` 与 `book_maturity_view_v2` 详述 Plan111 的输入、组件顺序、任务约束，禁止回退到 reasons[]/Plan102。

## Consequences / 影响

- **正面：** Product 可以从组件 detail 直接定位“结构缺口 vs 活动不足”，运营在 Overview/BookMainWidget 两处看到一致的任务清单与分值拆解。
- **正面：** 数据合同稳定，前端不再重建分值或猜测任务；tooltip 语言与后端 detail 完全一致，方便国际化/后续 A/B 实验。
- **正面：** 手工加成收敛到 ±5，既保留人工判定空间，又避免越权导致 Stage 跳跃；`operations_bonus` 字段仍可追踪来源。
- **负面：** Score 组件数量增多，旧的 `reasons[]` 前端逻辑需要全部迁移；Playwright/RTL 基线需更新。
- **负面：** Plan111 blueprint 现阶段硬编码在仓库，后续若要自助配置，需要额外引入管理界面与版本控制。

## Implementation Notes / 实施

1. **Domain:**
   - 新建 `backend/api/app/modules/book/domain/services/plan111.py`，包含 snapshot、blueprint、score helpers。
   - `BookMaturityScoreService` 仅负责数据裁剪与 snapshot 构建，最终分值来自 `calculate_plan111_score`。
2. **Application:**
   - `CalculateBookMaturityUseCase` 构建 Plan111 snapshot，沿用 `PLAN111_STRUCTURE_TASKS` 计算任务状态；`derive_maturity_from_score` 输出 Stage。
   - `MaturitySnapshotDto` 仍保留 blocks/todos/tags 等指标，供 UI 诊断。
3. **Frontend:**
   - `frontend/src/features/maturity/model/api.ts` 中的 `normalizeScoreComponents` 与 DTO 对齐 `score.components`。
   - `MaturityScoreBreakdown` 根据 factor 选择 icon/label，并显示“人工加成/扣分”细节。
4. **Documentation/Test:**
   - DDD/Hex/Visual RULES 更新为 Plan111 语义，强调组件顺序不可在前端重排。
   - 新增 `backend/api/app/tests/test_maturity/test_plan111.py` 用例，覆盖结构/活动/质量/任务/人工加成的边界；前端手册 `libraryThemeManualCheck` 继续验证主题继承。
