---
id: spec-libraries-overview
title: Library Overview 行为规范
status: draft
version: 0.1.0
updated: 2025-12-18
relatedAdr:
  - adr-libraries-overview-stability
relatedChecklist:
  - ck-libraries-overview-regression
---

## 1. 范围（Scope）

**In scope**
- Admin 端 `/admin/libraries` 视图以及 `LibraryMainWidget`、`LibraryCard`、`LibraryCardHorizontal`。
- 搜索、排序、Pinned/Archived 切换、Basement CTA、卡片 hover 操作等行为。
- Description/Tags/封面等展示规则以及相应占位。

**Out of scope**
- Library Detail、Bookshelf、Basement 内部功能；
- Library 软删除与恢复（当前版本未实现，参见 Future Work）；
- 除列表以外的性能优化或推荐策略。

## 2. 页面结构

1. **Hero 区块**：
   - 标题、副标题、Search input（placeholder "Search libraries..."）。
   - 新建按钮 `+ New Library`。
2. **Controls**：
   - Sort 下拉（Last activity / Most viewed / Latest Created / Sort by name）。
   - `Show archived` toggle；`Grid/List` 切换按钮。
3. **列表区域**：
  - 分为 `All` 与 `Archived` 两段：
    - 所有未归档 Library 归入 All；
    - 归档 Library 归入 Archived，且仅在 `Show archived` 打开时显示。
  - Grid 与 List 两种布局，均读取同一数据集，并在各自分组内采用 pinned-first 排序。
4. **Basement CTA**：
   - 文案 `Deleted books or libraries? Go to Basement recycle →`。
   - 整块为按钮，点击跳转 Basement 页面。

## 3. 交互规范

### 3.1 加载与偏好持久化（LIB-OVW-LoadingVisible, LIB-OVW-ViewSwitchLoading）
- 初次加载展示 skeleton，最长 3 秒需要出现首屏内容。
- 视图、排序、是否包含归档通过 localStorage 持久化，刷新后立即生效。
- Grid/List 切换带有淡入过渡，不允许出现长期空白。

### 3.2 搜索（LIB-OVW-SearchWorks）
- 输入后 Enter 或点击按钮，将 query 写入 URL `?q=` 并触发刷新。
- 结果列表必须只包含名称或描述包含关键字的 Library；若无结果显示空态。

### 3.3 创建/编辑/标签（LIB-OVW-CreateVisible, LIB-OVW-EditPersists, LIB-OVW-TagsPlaceholder）
- `LibraryForm` 采用同一组件：
  - 编辑时加载现有值，清空 description 会发送空字符串让后端移除。
  - 保存成功立刻关闭弹窗并刷新列表缓存，用户无需刷新页面。
- 无标签时隐藏 chips 区域并展示 `— No tags` 占位。

### 3.4 Pin / Archive（LIB-OVW-SectionPartitioned, LIB-OVW-PinArchiveRealtime）
- Hover 卡片右上角依次显示按钮：PIN → ARCHIVE → COVER → EDIT → DELETE；List/Grid 顺序一致。
- Pin 成功后：
  - 该库在所属分组（All / Archived）内采用 pinned-first 排序，立即移动到当前分组顶部；
  - 卡片角落出现 `Pinned` 徽标。
- Archive 成功后：
  - 卡片移动至 Archived 段并显示 `Archived` 徽标；`Show archived` 关闭时隐藏。
- 取消 Pin/Archive 时，卡片返回 All 段并按 pinned-first + 最近更新时间顺序排布。

### 3.5 卡片内容（LIB-OVW-InfoConsistent, LIB-OVW-StatusMetaAccurate）
- Title 单行显示，超出用省略号；点击进入详情。
- Description：
  - 若有内容显示一行文本，超出截断；
  - 若为空，显示 `— No description` 占位。
- Tags：最多展示 3 个 chips，超出显示 `+N`。
- 状态条：包含书本数量、Created、Updated、Views（若缺失显示 `no data`）。
  - Bookshelves 指标默认最少为 1，表示系统自带的 Basement bookshelf。

### 3.6 封面与占位（LIB-OVW-CoverPlaceholder, LIB-OVW-CoverCrop, LIB-OVW-ScrollNoJank）
- Grid 使用 16:9 封面；List 使用 40x40 头像。
- 图片加载失败时立即 fallback 到默认渐变背景，并记录一次警告。
- 滚动中高度保持固定，禁止抖动或 reflow。

### 3.7 Basement CTA（LIB-OVW-BasementLinkWorks）
- CTA 整块具有 hover/active 状态，点击后导航到 Basement recycle 页面。

### 3.8 错误与性能（LIB-OVW-NoErrorsInConsole, LIB-OVW-HomeScreenDisplay, LIB-OVW-NoHighLantency）
- 正常操作过程中浏览器控制台不得出现未捕获错误。
- 列表 API 在标准网络下响应时间需保持可接受（<1s 平均），否则记录 issue。

## 4. Checklist 对照

| 能力 | Checklist ID | 备注 |
| --- | --- | --- |
| 视图/偏好加载 | LIB-OVW-LoadingVisible | Grid/List + sort + archived toggle | 
| 搜索过滤 | LIB-OVW-SearchWorks | Search input 与 URL 同步 |
| 创建/编辑一致性 | LIB-OVW-CreateVisible / LIB-OVW-EditPersists | 含 description placeholder |
| Pinned/Archived 分层 | LIB-OVW-SectionPartitioned / LIB-OVW-PinArchiveRealtime | 含徽标与自动刷新 |
| 卡片 hover 操作 | LIB-OVW-CardHoverActions | 顺序固定，tooltip 完整 |
| 占位与封面 | LIB-OVW-DescPlaceholder / LIB-OVW-CoverPlaceholder | 同时适用于 List/Grid |
| Basement CTA | LIB-OVW-BasementLinkWorks | 跳转 basement |
| 错误性能 | LIB-OVW-NoErrorsInConsole / LIB-OVW-HomeScreenDisplay | 运行期保障 |

## 5. Verification（ck-run 指南）

- 每次回归必须执行 `ck-libraries-overview-regression`，并在 ck-run 记录通过/失败/N/A。 
- 若检查失败，需引用 issue ID（例如 `ISS-LIB-COVER-RATIO`）。
- 若能力未实现（如软删除），必须写明 N/A 原因 + 对应 issue。

## 6. Future Work

- **Library 软删除与恢复（LIB-OVW-DeleteGone）**：
  - 计划采用软删除字段 + Basement 列表恢复；
  - 目前按钮为占位，功能未启用，ck-run 标记 N/A；
  - 待 ADR / SPEC 更新后再纳入回归范围。
- **封面裁剪策略升级**：参见 issue `ISS-LIB-COVER-RATIO`。
