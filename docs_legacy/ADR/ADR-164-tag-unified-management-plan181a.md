# ADR-164 Plan181A Tag Unified Management

## Status

Status: Accepted
Date: 2025-12-08
Authors: Platform Tag Experience WG (Plan181A)

## Context

1. **Tag 描述来源分裂。** Library、Bookshelf、Book UI 早期各自拼接 tooltip 文案，部分页面仍直接调用 `/tags` 或写死「DEV｜开发冲刺」等翻译，导致描述错乱且无法追踪真源。
2. **书籍/书橱 DTO 已限定为 `tags_summary: string[]`，但 UI 仍想要颜色/描述信息。** 没有统一管道时，就会在 Preview 组件、Basement 视图或表单里重复拉取 Tag 数据。
3. **标签创建流程缺乏共用 helper。** LibraryForm、BookshelfTagEditDialog、BookEditDialog 都有“输入名称→若不存在就创建”一段代码，分散实现难以维护。

## Decision

1. **单一数据源。** Tag 描述只能来自 Tag 模块（`tags` 表）通过 LibraryTagSummary 投影出来的 `description` 字段；Book/Bookshelf 只携带名称列表。Tooltip 逻辑统一在新 helper（`tagTooltipHelper` + `TagViewModel`）里处理，UI 不再硬编码翻译。
2. **Catalog hook。** `useLibraryTagCatalog(libraryId)` 负责在 React Query 层缓存 Library Catalog，合并 inline tags + API 结果，并在缺失描述时触发一次 `searchTags(keyword)` 兜底。返回值提供 `tagDescriptionsMap`（unscoped + scoped key）供所有 Preview/Tooltip 消费。
3. **共享 tag-id helper。** Library/Bookshelf/Book 表单通过 `ensureTagIds` 把自由文本解析成 tag_id（先 search，找不到才 create），再调用既有 replace/associate API，保持“后端只认 ID” 的契约。
4. **缓存失效规范。** /admin/tags 页面成功更新描述或颜色后必须 `invalidateQueries(['library-tag-catalog'])`，确保 Library/Bookshelf/Book 视图同步刷新。

## Consequences

* **正向:** 所有 tooltip 与 aria-label 都能追溯到 Tag 管理端的真实文案；中英文界面保持一致，再也不会出现“DEV 标签在某个页面只有英文”的问题。
* **正向:** Preview 组件完全解耦数据抓取逻辑，BookMainWidget/BookshelfDashboard 只需一次 hook 即可下发描述映射。
* **正向:** Tag 创建/关联流程复用 `ensureTagIds`，避免出现「Library 可以创建新标签但 Book 无法」的功能差异。
* **负向:** Catalog hook 在缺失描述时会额外命中 `/tags` 搜索接口；需要关注热门 Library 的缓存命中率，必要时扩容 Redis/HTTP 缓存。

## Implementation Notes

* Frontend: `frontend/src/features/library/model/hooks.ts` 新增 global catalog fetch 流程（React Query key `['library-tag-catalog', libraryId]` + `searchTags` fallback），并导出 `tagDescriptionsMap` 给 Bookshelf/Book 视图。
* Frontend UI: `BookMainWidget`, `BookshelfDashboardBoard`, `/admin/books` 页都通过 hook 注入描述 map；`BookPreviewList/Card`, `BookRowCard`, `BookFlatCard` 仅消费 map，不再各自请求。
* Shared helpers: `frontend/src/features/tag/lib/tagCatalog.ts` 集中 `buildTagDescriptionsMap / merge / resolve / findMissing`；`tagTooltipHelper`（TODO 下一步）承载 label/description 拼接与 aria 生成。
* Docs: `Plan_180A`, `Plan_181A`, `DDD_RULES.yaml`, `HEXAGONAL_RULES.yaml`, `VISUAL_RULES.yaml` 已记录本决策的约束与 UI 期望。

## References

* `Plan_181A_TagUnifiedManagement.md`
* `Plan_180A_ZH-EN-Basement&TagSystemPreview.md`
* `frontend/src/features/library/model/hooks.ts`
* `assets/docs/DDD_RULES.yaml`
* `assets/docs/HEXAGONAL_RULES.yaml`
* `assets/docs/VISUAL_RULES.yaml`
