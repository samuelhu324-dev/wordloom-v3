```markdown
// filepath: d:\Project\Wordloom\backend\storage\assets\checklist\regression\ck-libraries-overview-regression.md
---
id: ck-libraries-overview-regression
title: Library Overview 回归检查清单
type: regression
---

## 一、核心操作路径

- [ ] Grid 和 List 能正常加载 Library 列表，无明显报错或空白区域；再次打开页面沿用上次选择的视图模式（Grid/List）。 [LIB-OVW-LoadingVisible]
- [ ] 新建 Library → 返回 Overview 后能直接看到新条目，无需手动刷新 [LIB-OVW-CreateVisible]
- [ ] 编辑 Library 的 Title / Tags / Description → 刷新页面后内容保持一致 [LIB-OVW-EditPersists]
- [ ] 编辑 Library 的 Tags 并点击 Save → 当前页面不做硬刷新时，Grid / List 中该条 Library 的标签立即更新（不再显示旧标签或 “— No tags”）[LIB-OVW-TagsRealtime]
- [ ] “Search libraries…” 输入关键字后能基于 Title + Description 进行过滤，结果与搜索词匹配 [LIB-OVW-SearchWorks]
- [ ] 点击 Grid 卡片或 List 行，能够进入正确的 Library 详情页 [LIB-OVW-LibraryClickable]
- [ ] 底部 “Deleted books or libraries? Go to Basement recycle →” CTA 可点击并跳转到 Basement 页面 [LIB-OVW-BasementLinkWorks]

## 二、信息展示

- [ ] 同一条 Library 在 Grid 和 List 中的标题、标签、描述整体一致，没有明显错配 [LIB-OVW-InfoConsistent]
- [ ] 没有 Tags 的 Library，展示占位文案 “— No tags”，整体布局不塌陷 [LIB-OVW-TagsPlaceholder]
- [ ] Description 为空时，展示占位文案 "— No description" [LIB-OVW-DescPlaceholder]
- [ ] Description 较长时，截断和省略号正常，不遮挡其他信息 [LIB-OVW-DescrDetailSaved]
- [ ] 卡片上的图标与按钮（含 tooltips）在 Grid 和 List 中都能正常显示与触发 [LIB-OVW-TooltipsVisible]
- [ ] Hover 卡片时右上角依次出现 PIN / ARCHIVE / COVER / EDIT / DELETE 图标，交互可点击 [LIB-OVW-CardHoverActions]
- [ ] 卡片下方的状态栏（如书本数量、创建/更新时间、浏览次数）信息正确、与真实数据匹配 [LIB-OVW-StatusMetaAccurate]
- [ ] 新建 Library 默认包含 Basement Bookshelf，状态栏书架数量至少为 1（Basement）[LIB-OVW-BasementBookshelfDefault]

## 三、筛选与状态栏

- [ ] 顶部状态栏（Latest activity / Most viewed / Latest Created / Sort by name 与 Show archived）切换后，列表内容与状态匹配 [LIB-OVW-StatusFiltersWork]
- [ ] 页面顶部的 All / Archived 分组展示与实际数据一致（Archived 只含归档，All 不遗漏）[LIB-OVW-SectionPartitioned]
- [ ] 执行 Pin/Unpin 或 Archive/Restore 后，列表自动刷新，徽标与分组归属实时更新，取消操作回归 All [LIB-OVW-PinArchiveRealtime]
## 四、封面与占位图

- [ ] 无封面 Library 在两种视图中都展示统一占位图，不出现闪烌或空白块 [LIB-OVW-CoverPlaceholder]
- [ ] 更新 / 切换封面图后，刷新页面仍显示新封面 [LIB-OVW-CoverSwitchPersist]
- [ ] 插入/更新封面图后，在 Grid 与 List 视图之间切换时依然显示最新封面，不回退或丢失 [LIB-OVW-CoverViewTogglePersist]
- [ ] 列表滚动时，封面/头像不抖动或改变尺寸 [LIB-OVW-ScrollNoJank]

## 五、模式与刷新体验

- [ ] 在 Grid / List 之间切换时，有合理的加载或过渡状态，不出现长期空白 [LIB-OVW-ViewSwitchLoading]

## 六、错误与性能

- [ ] 浏览器控制台在正常浏览和操作过程中无未处理 error（与该页面相关）[LIB-OVW-NoErrorsInConsole]
- [ ] 主要列表接口请求在正常网络下响应时间可接受，延迟异常不高[LIB-OVW-NoHighLantency]
- [ ] 首次进入页面时，首屏内容在3秒显现 [LIB-OVW-HomeScreenDisplay]

## 七、未来能力（当前版本未实现，仅预留 ID）

- [ ] Library 支持软删除与 Basement 恢复：删除后从 Overview 中消失，可在 Basement 中查看并恢复 [LIB-OVW-DeleteGone]
- [ ] 有封面 Library 在 Grid 中展示封面，在 List 中展示头像，采用统一裁剪策略（待新规范）[LIB-OVW-CoverCrop]

## 八、自动化覆盖（Playwright）

- [ ] `LIB-OVW-CreateVisible`：`frontend/tests/e2e/library-overview.spec.ts` → "新建后能直接看到" 用例。
- [ ] `LIB-OVW-TagsPlaceholder`：同上文件 → "无 Tags 显示 — No tags" 用例。

运行步骤：
1. 在一个终端启动前端：`npm run dev`（需确保 baseURL 指向本地地址）。
2. 新终端执行：`npm run test:e2e` 即可跑完上述用例，也可使用 `npx playwright test --grep LIB-OVW` 单独过滤。
```