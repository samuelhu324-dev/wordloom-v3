---
id: ck-bookshelf-overview-regression
title: Bookshelf Overview 回归检查清单
type: regression
---

## 一、核心操作路径

- [ ] 首次加载时能正常渲染书橱列表（仅 List 模式），无明显报错或空白区域 [BSH-OVW-LoadingVisible]
- [ ] 点击 "新建书橱" 完成创建后，无需刷新即可在当前 Overview 中看到新书橱，数量统计与进度条同步更新 [BSH-OVW-CreateVisible]
- [ ] 点击任意书橱，能够进入对应书橱详情或书本列表视图（视实现而定）[BSH-OVW-BookshelfClickable]

## 二、信息展示

- [ ] 书橱卡片上的书本数量、状态（Active / Archived）、最近更新时间等元信息与后端数据一致（无 description 展示）[BSH-OVW-StatusMetaAccurate]

## 三、筛选与排序

- [ ] 切换排序选项（最近更新 / 名称 A-Z / 书本数量）后，列表顺序与选项含义匹配（不持久化用户偏好）[BSH-OVW-SortOptionsWork]
- [ ] 切换状态筛选（All / Active / Archived）后，列表仅展示满足条件的书橱；无结果时展示统一空态 "No bookshelves yet" [BSH-OVW-StatusFilterWorks]

## 四、容量与告警

- [ ] 当书橱总数接近上限（>= 80）时，顶部进度条与文案提示正常展示，文案与当前数量匹配 [BSH-OVW-LimitWarningVisible]
- [ ] 当书橱数量达到上限（>= 100）时，"新建书橱" 按钮禁用且带有明确提示文案，不会再发起创建请求 [BSH-OVW-LimitReachedDisabled]

## 五、错误与降级

- [ ] 后端返回错误（例如 4xx/5xx）时，Bookshelf 区域展示明显的错误提示块，包括 HTTP 状态码与后端 detail 信息（若存在）[BSH-OVW-ErrorBannerVisible]
- [ ] 错误状态下书橱列表为空渲染但组件不崩溃，页面其他区域可继续使用 [BSH-OVW-ErrorStateIsolated]
- [ ] 正常浏览和操作 Bookshelf Overview 时，浏览器控制台无与该组件相关的未处理 error [BSH-OVW-NoErrorsInConsole]

## 六、未来能力（当前版本未完全实现，仅预留 ID）

- [ ] 书橱支持 Pin/Unpin，并在列表中采用 pinned-first 排序，逻辑复用 Library 卡片（待实现）[BSH-OVW-PinOrdering]
- [ ] 书橱级标签展示与 Library 标签规范保持一致（占位文案、最多展示数量等，待实现）[BSH-OVW-TagsDisplay]

## 七、自动化覆盖（Playwright / Vitest）

- [ ] `BSH-OVW-CreateVisible`：后续可在 `frontend/tests/e2e` 中补充 Bookshelf Overview 场景，用例命名约定为 `BSH-OVW-CreateVisible`。（当前未实现自动化，ck-run 标记 N/A）
- [ ] `BSH-OVW-StatusFilterWorks`：建议补充对 Active / Archived 筛选的端到端用例。（当前未实现自动化，ck-run 标记 N/A）

运行建议：
1. 在本地启动前端与后端，进入任意 Library 详情页，确保嵌入的 `BookshelfMainWidget` 加载完成；
2. 按上述检查项由上到下操作一次，将结果记录在对应 ck-run 文件中（如 `ck-run-bookshelf-overview-YYYY-MM-DD.md`）。
