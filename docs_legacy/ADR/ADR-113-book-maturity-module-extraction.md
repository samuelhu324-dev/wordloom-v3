# ADR-113: Book Maturity Module Extraction

- Status: Accepted (Nov 28, 2025)
- Deciders: Wordloom Core Team
- Context: Plan98 (Refactoring Maturity), ADR-092/ADR-111 (maturity scoring & coverage), ADR-093 (Chronicle timeline), DDD_RULES `POLICY-BOOK-MATURITY-*`
- Related Artifacts: migration `029_create_maturity_snapshots.sql`, modules `api.app.modules.maturity.*`, DI container `dependencies_real.py`, DDD_RULES `POLICY-BOOK-MATURITY-MODULE-SPLIT`

## Problem

1. **聚合耦合**：成熟度评分（BookMaturityScoreService）与任务推荐散落在 `modules/book` 内，所有 API/UseCase 都通过 Book 聚合暴露，导致成熟度相关改动必须触碰书籍核心模块。
2. **缺乏快照**：成熟度得分只有 Book.maturity_score 当前值，没有历史快照；前端无法追溯“为何昨天还在 Growing 今天就进 Stable”。
3. **端点混杂**：`/api/v1/books/*` 承载了“重算成熟度、更新成熟度、查询成熟度”多种职责，违背 Hexagonal“单一端口 = 单一聚合”的目标。
4. **任务建议无规范**：结构任务 (Next Steps) 逻辑散布在 UI，缺少集中策略文件来约束“缺摘要/缺标签/有 TODO”时的提示顺序与长度。

## Decision

建立独立的 **Maturity 模块**，遵循以下拆分：

1. **Domain 层**
   - `MaturityStage`/`MaturityScore`/`TransitionTask`/`MaturitySignals` 等价值对象位于 `modules/maturity/domain`。
   - `MaturityRuleEngine` 封装既有 `BookMaturityScoreService`，专注 0-100 分计算与 stage 映射。
   - `MaturityTransitionPolicy` 根据信号（标题/摘要/标签/封面/TODO/Block 数）输出最多两条任务建议，规则写入 DDD_RULES。

2. **Application 层**
   - `BookAggregateMaturityDataProvider` 从 BookRepository 读取聚合及其快照字段，统一转换为 `BookProfileSnapshot` + `MaturitySignals`。
   - `CalculateBookMaturityUseCase`：输入 book_id，调用 provider → rule engine → policy → 构造 `MaturitySnapshot`，可选持久化。
   - `ListMaturitySnapshotsUseCase`：仅负责从快照仓库分页读取历史。

3. **Infrastructure 层**
   - 新建表 `maturity_snapshots`（book_id, stage, score, components JSONB, tasks JSONB, manual_override, manual_reason, created_at）。
   - `SQLAlchemyMaturitySnapshotRepository` 负责 JSON ↔ dataclass 转换与查询排序；禁止在 Repository 中嵌入评分逻辑。
   - 迁移脚本 `029_create_maturity_snapshots.sql` 由应用启动时自动回放。

4. **API / DI**
   - FastAPI 路由 `/api/v1/maturity/books/{bookId}/evaluate` 与 `/snapshots` 暴露只读端口；所有成熟度相关数据访问都通过该模块完成。
   - DI 容器新注册 `maturity_data_provider` 与 `maturity_snapshot_repo`，并提供 `get_calculate_book_maturity_use_case` / `get_list_maturity_snapshots_use_case` 工厂。

## Consequences

- **正向**
  - 成熟度评分/任务建议拥有独立生命周期，可在不触碰 Book 核心的情况下快速试验规则。
  - 快照表为未来“成熟度趋势图、调试视图”提供基础数据；任务建议也可通过快照 API 暴露。
  - API 语义清晰：Book 模块继续负责 CRUD / 手动 override，Maturity 模块负责评分与历史。

- **负向**
  - 需要维护额外的 migration 和 Repository，初期会增加数据库表数量。
  - Provider 仍依赖 BookRepository，加大了 Book 聚合字段缺失时的错误面，需要更多测试覆盖。

## Implementation Notes

1. **目录结构**
   - `backend/api/app/modules/maturity/domain|application|routers`，保持与其他模块相同的 Hexagonal 层次。
   - `infra/database/models/maturity_models.py` + `infra/storage/maturity_repository_impl.py` 实现持久层。
2. **路由与依赖**
   - `main.py` 注册 maturity router；`dependencies_real.py` 创建 data provider + repository。
   - 所有评估请求返回 `MaturitySnapshotSchema`（score + components + tasks + override 标记）。
3. **规则同步**
   - DDD_RULES 新增 `POLICY-BOOK-MATURITY-MODULE-SPLIT`，交代边界/表结构。
   - 后续若成熟度模块需要写回 Book 聚合，必须通过既有 UseCase，而不是在模块内直接操作 `books` 表。
4. **测试 & 回滚**
   - 在回滚或未启用 snapshot 表的环境下，可关闭 `persist_snapshot` 参数（默认 true）以避免写入失败；UseCase 在 repository 缺失时仍能返回评分结果。
