---
id: adr-libraries-overview-stability
title: Library Overview 稳定性改造
status: accepted
date: 2025-12-18
related:
  - ck: ck-libraries-overview-regression
  - spec: spec-libraries-overview
---

## 1. 背景（Context）

Library Overview 是进入 Wordloom 工作区的默认落点。过去数月暴露出以下高频缺陷：

- Grid/List 渲染使用不同字段与缓存，导致标题、标签、描述不一致，`LIB-OVW-InfoConsistent` 连续失败。
- 加载偏好（视图模式 / 排序 / Archive filter）与搜索框状态不会持久化，用户每次进入都需重设，`LIB-OVW-LoadingVisible` 与 `LIB-OVW-SearchWorks` 体验不佳。
- 无封面或加载失败时出现空白、破图，Description 为空时显示旧内容或 `undefined`，直接影响 `LIB-OVW-DescPlaceholder`、`LIB-OVW-CoverPlaceholder`。
- Pin / Archive 操作需要整页刷新才生效，无法即时回到正确分组，`LIB-OVW-PinArchiveRealtime` 与 `LIB-OVW-SectionPartitioned` 风险高。
- 删除按钮目前只做占位，缺少 Library 级软删除与 Basement 恢复链路；此能力暂未规划进当前冲刺，但需要在检查清单里显式标注。

因此，本 ADR 需要明确：当前版本聚焦“可见性与一致性”的稳定性改造，同时把软删除等未来能力隔离在计划列表里。

## 2. 决策与目标（Decision / Goals）

1. **数据与交互一致性**：Grid 与 List 共用同一查询、缓存与字段映射；创建、编辑、Pin、Archive 在成功后应立即反映在 UI。  
   - 关联 ck：`LIB-OVW-LoadingVisible`、`LIB-OVW-CreateVisible`、`LIB-OVW-PinArchiveRealtime`。
2. **展示与占位可预期**：Description、Tags、封面/头像在任何状态下都有合理 fallback，Hover 操作入口完整。  
   - 关联 ck：`LIB-OVW-DescPlaceholder`、`LIB-OVW-CardHoverActions`、`LIB-OVW-CoverPlaceholder`。
3. **治理可追踪**：所有可回归项都拥有唯一 ID，记录在 `libraries-overview-ids.json`，并由回归清单与 SPEC 双向引用。  
4. **明确范围边界**：Library 软删除（`LIB-OVW-DeleteGone`）保持为未来能力，回归执行时标记为 N/A，避免误报失败。

## 3. 技术与产品方案概要

### 3.1 数据层与缓存

- Grid/List 使用统一 React Query key（`['libraries', query, sort, includeArchived]`），并在视图切换时共享缓存。
- 将视图模式、排序、是否显示归档持久化在 `localStorage`（键：`wl_libraries_view` 等），满足 `LIB-OVW-LoadingVisible`。
- Search 输入与 URL 同步（`/admin/libraries?q=...`），提交后刷新查询，支撑 `LIB-OVW-SearchWorks`。

### 3.2 交互流程

- `LibraryForm` 在编辑模式下对 description 发送空字符串即可清空，保障 `LIB-OVW-DescPlaceholder`。
- Pin/Archive 使用 `useQuickUpdateLibrary`，在 `onSuccess` 中直接更新缓存 + invalidation，确保操作立刻反映到 Pinned/All/Archived，满足 `LIB-OVW-PinArchiveRealtime`。
- Hover 动作按钮（PIN / ARCHIVE / COVER / EDIT / DELETE）在组件层统一顺序，并挂接 tooltip、accessibility label。

### 3.3 展示与占位

- 封面/头像组件加 onError fallback，退回默认渐变；列表滚动使用固定 aspect ratio 与尺寸，满足 `LIB-OVW-CoverPlaceholder`、`LIB-OVW-ScrollNoJank`。
- Description、Tags、状态条（书本数/创建更新/浏览次数）统一格式化函数，防止值缺失时渲染异常。
- 底部 CTA “Go to Basement recycle” 维持可点击，跳转 basement 页面，覆盖 `LIB-OVW-BasementLinkWorks`。

### 3.4 Checklist / ID 治理

- `backend/storage/assets/checklist/regression/ck-libraries-overview-regression.md` 是执行清单。  
- `backend/storage/assets/checklist/index/libraries-overview-ids.json` 维持所有 ID、状态、所属分区。  
- SPEC（见 `spec/spec-libraries-overview.md`）描述预期行为与 ID 对应关系。  
- ck-run 模板要求：若某能力（如 `LIB-OVW-DeleteGone`）未实现，必须在结果中注明 N/A 与关联 issue。

## 4. 验收标准（Acceptance）

验收以 ck-libraries-overview-regression 为准，至少需覆盖：

- `LIB-OVW-LoadingVisible`：重新进入页面保留视图/排序偏好，Grid/List 无空白。
- `LIB-OVW-CreateVisible` + `LIB-OVW-EditPersists`：创建与编辑后，无需手动刷新即可看到最新数据。
- `LIB-OVW-SearchWorks`：Search 框过滤结果准确。
- `LIB-OVW-PinArchiveRealtime`：Pin/Archive/Restore 后即时移动到对应分组并展示徽标。
- `LIB-OVW-DescPlaceholder`、`LIB-OVW-CardHoverActions`、`LIB-OVW-StatusMetaAccurate`：展示信息与操作入口全部可用。
- `LIB-OVW-BasementLinkWorks`：Basement CTA 正确跳转。
- 错误与性能：`LIB-OVW-NoErrorsInConsole`、`LIB-OVW-HomeScreenDisplay` 通过。

`LIB-OVW-DeleteGone` 等未来能力在 ck-run 中需标记为 N/A 并引用后续计划。

## 5. 风险与回滚

- **统一缓存风险**：若查询 key 或数据映射出错，会让 Grid/List 同时挂掉。回滚方式：恢复旧的分离缓存实现，并关闭偏好持久化逻辑。
- **即时更新风险**：Pin/Archive 依赖局部缓存写入，若写入逻辑 bug 可能导致视图与服务器状态不一致。回滚方式：移除局部写入，仅保留 `invalidateQueries`。
- **占位策略风险**：错误的 onError fallback 可能导致无限触发。回滚方式：关掉图片 fallback，只展示纯色背景。

## 6. 后续与未来能力

- Library 软删除 + Basement 恢复（`LIB-OVW-DeleteGone`）暂不实现，保留 issue `ISS-LIB-DELETE` 跟踪；ck-run 标为 N/A。
- 未来迭代需追加新的 ADR 或更新本 ADR，描述软删除字段、API、Basement UI 以及新的回归项。
- SPEC 中应继续维护 “Future Work” 小节，确保设计与实现对齐。