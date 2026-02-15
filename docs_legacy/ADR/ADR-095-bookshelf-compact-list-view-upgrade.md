# ADR-095: Bookshelf Compact List View Upgrade (Plan47)

- Status: Accepted (Nov 24, 2025)
- Deciders: Wordloom Core Team
- Context: Plan47_BookshelfPreview, VISUAL_RULES, HEXAGONAL_RULES
- Related: ADR-094 (Library Bookshelf Dashboard & Theme Integration)

## Context

在 Library 详情页，现有 Bookshelf 列表同时提供“紧凑视图/舒适视图”。
实践发现舒适视图信息密度低、维护两套 UI/交互成本高，且不利于展示成熟度分布与最近活动。
同时，卡片“墙面色”需从 Library 的主题色继承，但这属于纯视觉规则，不能下沉为领域数据。

## Decision

1) 仅保留“紧凑视图”作为唯一工作视图，移除“舒适视图”切换入口与实现（标记 deprecated 并删除 UI 入口）。
2) 左侧缩略图升级为 96×96（允许 88×88 最小兼容），内容为透明书柜 PNG + Library 主题色生成的墙面渐变。
3) 颜色继承在前端完成：cover → library_theme（含预设 silk-blue）→ hash，使用 CSS 变量注入，不新增/持久化后端字段。
4) 中间信息区改为三行：标题+状态Chip、Tags（最多3个）/“无标签”、成熟度汇总（🌱Seed · 🌿Growing · 📘Stable · 📦Legacy）。
5) 右侧展示关键统计 + Chronicle 摘要：总书数、近7天活跃、今日次数；最近事件相对时间 + 类型。

## Rationale

- “工作视图”优先信息密度与扫读效率，统一视觉语言减少学习与维护成本。
- 颜色继承为展示属性，避免跨聚合写入导致数据不一致与迁移复杂度。
- 与 Plan47 的结构保持一致，利于后续引入搜索/筛选/排序的一致交互。

## Scope

- Frontend（Presentation 层）实现；Backend/Domain 无需变更。
- 主题与颜色计算在前端：CSS 变量 + 本地缓存（`wl_library_theme_*`）。

## Non-Goals

- 不引入后端颜色计算/持久化；不新增 Bookshelf.wall_color 等字段。
- 不实现新的权限/多租户逻辑。

## UX Spec（摘要）

- 左侧缩略图：96×96 透明书柜 PNG；背景渐变从 Library 主题色导出并柔化（不改变 Hue）。
- 中间三行：
  - 行1：名称（加粗） + 状态Chip（ACTIVE/FROZEN/ARCHIVED）。
  - 行2：最多 3 个 Tag；缺省显示“无标签”。
  - 行3：成熟度汇总：🌱Seed · 🌿Growing · 📘Stable · 📦Legacy。
- 右侧两行：
  - 行1：📚总数、🕒近7天活跃、👁今日次数。
  - 行2：Chronicle 最近事件摘要（相对时间 + 类型）。
- 图标与色彩：
  - Seed=Sprout #8BC34A；Growing=TreeDeciduous #26A69A；Stable=BookOpen/ShieldCheck #2196F3；Legacy=Archive #FFB74D。
- 可访问性：成熟度图标 aria-label；Chronicle 列表 aria-live=polite。

## Architecture Alignment

- Hexagonal：展示层变更；无新增端口/适配器；Theme 通过 `data-theme` 与 CSS 变量注入。
- DDD：明确颜色继承为 UI 规则；后端不存储 wall_color；聚合边界不变。

## Implementation Notes

- 移除“舒适视图”切换及对应组件（或标记 deprecated 并隐藏）。
- 升级 Bookshelf 行组件布局与样式；引入 96×96 缩略图容器；采用现有主题 hook（cover→theme→hash）。
- 在 Library 详情页容器设置 `--library-theme-color` 等 CSS 变量供子组件使用。
- 渐变生成仅动 S/L，不改 H；失败回退 Silk Blue（#2e5e92）。
- 缓存：内存+localStorage；跨刷新稳定主题色。

## Risks & Mitigations

- 风险：错误将展示色写入后端；治理：代码审查 + DDD_RULES 新增禁止策略。
- 风险：跨域图片取色失败；治理：超时回退主题色，域名白名单按需配置。

## Rollback

- 如需恢复舒适视图，可从 git 历史恢复组件，但默认入口仍保持隐藏。

## Test Plan

- Snapshot：空态/有数据/不同成熟度组合。
- Interaction：分页加载一次；切换排序主题色不变；Chronicle 提要渲染正确。
- A11y：aria-label/aria-live 验证；对比度≥4.5。

## References

- Plan_47_BookshelfPreview.md
- VISUAL_RULES.yaml → `bookshelf_compact_list_view`
- HEXAGONAL_RULES.yaml → `library_bookshelf_dashboard_theme.compact_list_view_alignment`
- DDD_RULES.yaml → `POLICY-VISUAL-COLOR-INHERITANCE`, `POLICY-BOOKSHELF-COMPACT-VIEW-ONLY`
