
-
# Plan 180A · ZH-EN Basement & Tag System Preview

## 背景 · Background
- Basement（「回音室」）与 Bookshelf/Book 预览共享同一批标签，但在中英双语切换时，描述文案与 Tooltip 呈现常被不同组件各自实现，导致同一标签在 Basement 里丢失说明、在 Bookshelf 中又出现另一套格式。
- Tag 系统经过 Plan175/176 的梳理后已经具备 LibraryTagSummary + 全局 Tag Catalog，本计划要把这套真源应用在 Basement 视图与 Preview 组件，确保「库内标签摘要」与「真实 Tag 字典」统一供给。
- 结合 i18n Plan174/177，以「中英并行信息架构」为前提，让 Tooltip 与可视化副本都只依赖真实描述，不再硬编码翻译。

## 目标 · Goals
1. **Preview 一致性**：Basement 与 Bookshelf/Book Preview 使用同一套 Tag 描述/Tooltip helper，移除各组件内的局部拼接逻辑。
2. **双语可信度**：中英文界面都展示 Tag 管理端填写的原文；若需要双语说明，由 Tag 维护者直接在描述字段编写，而非 UI 侧复制。
3. **数据真源**：所有 Tooltip 数据都来自 LibraryTagSummary → TagCatalog hook，Basement/Preview 仅消费映射结果，不再额外请求或写死描述。

## 范围与步骤 · Scope & Steps
### Step 1 – 数据渠道梳理
- 为 Basement/Preview 注入 `useLibraryTagCatalog(libraryId)`，合并 inline tags 与远端 catalog。
- 输出 `tagDescriptionsMap`（unscoped + scoped key），供组件按照 `libraryId:label` 命中。

### Step 2 – UI Helper 对齐
- 在 Preview（BookMainWidget、BookDisplayCabinet、BookFlatCard/Card）与 Basement 列表中统一调用描述映射，tooltip 文案通过 i18n key：`books.tags.label` / `books.tags.withDescription`。
- Tooltip 仅显示 Tag 管理端的文本，不再自动追加翻译；若无描述则保持 label-only。

### Step 3 – 中英体验确认
- 验证 Bookshelf Dashboard、Basement 视图、/admin/books 与 Library 列表在 zh-CN 与 en-US 下的 Tooltip 行为一致。
- QA checklist：DEV/LOG 标签、ARCHIVED（系统标签）、自定义标签至少三例，确保 tooltip/aria-label 均指向 catalog 文案。

## 验收标准 · Acceptance
- ✅ `DEV`、`LOG`、`ARCHIVED` 等标签在 Basement/Preview 均展示来自 Library 的描述，无额外翻译或空 tooltip。
- ✅ 所有 Preview 组件的 tooltip 来源都可追溯到 `tagDescriptionsMap`，代码中不存在直接拼接 `label｜description` 的散落实现。
- ✅ 切换语言仅改变容器 copy，不改动 Tag 描述内容；无语言偏差或 fallback 文案。

## 风险 & 后续 · Risks & Follow-ups
- 缺失描述的标签将继续显示 label-only，需要 Tag 管理者在全局 catalog 中补录，这是产品流程而非技术 fallback。
- 当 LibraryTagSummary 缺失标签而 Bookshelf/Book 仍保留旧名称时，会触发 catalog fetch；需监控 Tag 查询的缓存命中率，避免对 `/tags` 造成额外压力。

## 实施进展 · Progress (2025-12-08)
- 引入 `useLibraryTagCatalog`（带 React Query 缓存）到 Bookshelf Dashboard、BookMainWidget，以及 /admin/books 视图，统一产出 `tagDescriptionsMap`。
- 所有 Book preview 组件（`BookPreviewList/Card`, `BookDisplayCabinet`, `BookFlatCard`, `BookRowCard`）已切换到映射驱动 tooltip；Basement Preview 复用同样的 map。
- 去除硬编码的「DEV｜开发冲刺」类双语 fallback，确保 tooltip 精确反映 Tag 维护者输入的内容。


