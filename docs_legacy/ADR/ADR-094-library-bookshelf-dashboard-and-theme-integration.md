# ADR-094 Library Bookshelf Dashboard and Theme Integration

Date: 2025-11-24
Status: Draft

## Context

Plan_44 和 Plan_46 定义了 /admin/libraries/[libraryId] 页面从“漂亮封面墙”升级为“书架运营面板 + Library 封面”的目标，需要把 Chronicle、Books 成熟度、Pinned/Archived 状态统一到一个看板上，同时遵守三份规则文件（DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES）里已有的分页与主题策略。

已有状态：
- Library 概览页已完成 pinned 分段、last_activity 排序和 archive 过滤（ADR-086，Plan20）。
- Bookshelf 列表端点已迁移到 Pagination Contract V2，并补充成熟度枚举（CONVENTION-ENUM-BOOK-MATURITY）。
- Library 封面采用 cover_large + cover_thumb 双规格（ADR-087），主题系统使用 CSS Variables + ThemeProvider（VISUAL_RULES.theme_system）。

本 ADR 需要明确：
1. Library Detail 页的 Bookshelf Dashboard 数据来源和 UseCase 边界；
2. Library 主色获取顺序（封面图 → theme_color → Hash fallback）；
3. Bookshelf 卡片视图/紧凑视图的布局与颜色策略；
4. 与三份规则文件的对齐方式。

## Decision

### D1. UseCase：GetBookshelfDashboard

- 新增 `GetBookshelfDashboardUseCase`（backend/api/app/modules/bookshelf/application/use_cases/get_bookshelf_dashboard.py），直接使用 AsyncSession 聚合：
  - 书籍成熟度：total / seed / growing / stable / legacy；
  - Chronicle 活跃度：edits_last_7d / views_last_7d / last_activity_at；
  - 书架属性：status / is_pinned / is_basement / created_at / updated_at；
  - 派生字段：health (active/slowing/stale/cold)。
- 过滤 & 排序 & 分页在 UseCase 内存层完成：
  - 过滤枚举：BookshelfDashboardFilter (all/active/stale/archived/pinned)；
  - 排序枚举：BookshelfDashboardSort (recent_activity/most_books/most_stable/most_active/longest_idle)；
  - 分页契约：Pagination Contract V2（request.page / request.size，response.total / items[]）。
- Basement 书架及软删除状态一律排除，保持与 POLICY-PERFORMANCE-DEGRADATION-SWRE 一致。

### D2. DTO：BookshelfDashboardItemDto

- 前端 `BookshelfDashboardItemDto` 与 UseCase 输出结构对齐，字段包括：
  - `id`, `library_id`, `name`, `description`, `status`；
  - `is_pinned`, `is_archived`, `is_basement`；
  - `book_counts`（total/seed/growing/stable/legacy）；
  - `edits_last_7d`, `views_last_7d`, `last_activity_at`, `health`；
  - 视觉扩展字段：`wall_color`, `base_color`（后端可选提供，前端总是有 fallback）。
- DTO 映射位于 frontend `entities/bookshelf`，仅负责命名和轻量转换，遵守“Adapter-Only Transformation”约定。

### D3. Library 主色获取顺序

- 新增 Library 主题策略（补充 HEXAGONAL_RULES.theme_runtime_strategy 与 VISUAL_RULES.theme_system）：
  1. **封面图优先**：
     - 如果 Library 存在 cover_large（16:9 横幅）或代表封面图，前端在 Library Detail 页加载该图片并通过 Canvas/Vibrant 提取主色；
     - 提取结果转为 HSL 三元组，写入页面根元素 CSS 变量：`--lib-h`, `--lib-s`, `--lib-l`。
  2. **主题色回退**：
     - 如果封面图不存在或提取失败，使用 `library.theme_color` 字段（十六进制字符串），在前端转换为 HSL 后写入同一组变量；
  3. **Hash Fallback**：
     - 如果以上两者均为空，则基于 `library.id` + `library.name` 使用稳定 Hash 生成 HSL，确保始终有主色；
- Library 主色的最终值只在客户端 Theme 层使用，不写回 Domain；后端如需长期持久化颜色，后续单独增加 Stats/Theme 聚合。

### D4. Bookshelf 卡片颜色和布局

- 所有 Bookshelf Dashboard 卡片统一使用 Wordloom “母书橱” PNG 作为前景图（1:1 比例），禁止为单个书架上传自定义封面，避免视觉割裂。
- 卡片背景由 Library 主色 + 书架微偏移组合而成：
  - 每个书架在主色基础上应用稳定 Hash 偏移：`hue_offset`（±12°/24°）、`sat_shift`（±5%）、`light_shift`（±8%）；
  - 在 CSS 中暴露为 `--shelf-h`, `--shelf-s`, `--shelf-l`，并用于线性渐变和色条；
- 视图模式：
  - **舒适视图 (comfortable)**：
    - 一行四张卡片（桌面端），封面区域使用 `aspect-ratio: 1 / 1` 的容器，母图居中 `object-fit: contain`；
    - 封面下方为信息区：书架名称 + 指标句（Books / Seed / Growing / Stable / Legacy + edits/views/health），遵循 VISUAL_RULES 的“不要画硬格子线”原则；
  - **紧凑视图 (compact)**：
    - 去掉大封面，仅保留左侧色条 + 一行文本指标，类似半表格；
    - 使用淡色 zebra 样式，但避免重线框，保持非 Excel 视觉。

### D5. Library 级看板与上限提示

- Library Detail 页顶部展示 Library 级看板：
  - 总书架数、Pinned 数、健康分布聚合自 Dashboard 快照（BookshelfDashboardSnapshot）；
  - 当 `total ≥ 80` 显示“接近上限”渐变提示条；当 `total ≥ 100` 显示“已达上限”并由前端禁用新建书架入口，对应 DDD_RULES 中 POLICY-BOOKSHELF-PINNED-SEGMENT 的上限 guard。

## Consequences

- 优点：
  - Library Detail 页从简单封面墙升级为包含 Chronicle + Books + 健康度的运营面板，与 Plan_13/Plan_44 预期一致；
  - 颜色系统有明确来源与回退路径：封面 → theme_color → Hash，不会出现“默认红灰渐变一统天下”的视觉问题；
  - Bookshelf 卡片视觉统一（母书橱 PNG），同时通过 Library 主色 + per-shelf 偏移提供可读的差异化；
  - 所有变更都遵循 Pagination Contract V2 和现有 DI/UseCase 边界，不破坏 Hexagonal 结构。
- 代价与风险：
  - 前端在 Library Detail 页增加了 Canvas/Vibrant 的运行成本，需要通过缓存（localStorage + libraryId→color）减轻重复计算；
  - 目前主色提取仅在前端完成，如需 SSR 一致色彩需后续在后端实现同样算法并持久化 theme_color；
  - Dashboard 仅统计当前分页范围内的书架，若未来允许 size < total 需要在后端增加专门的 Stats 聚合端点。

## Follow-up

- [ ] 在 HEXAGONAL_RULES.yaml 中记录 GetBookshelfDashboardUseCase 的端口和聚合责任。
- [ ] 在 VISUAL_RULES.yaml 中新增 Library Detail → Bookshelf Dashboard 的 UI 规则和颜色体系说明。
- [ ] 在 DDD_RULES.yaml 中补充 POLICY-BOOKSHELF-DASHBOARD，锁定 Pagination Contract V2 与 health 字段语义。
- [ ] 评估在 backend 增加异步任务，根据 cover_large 预计算并持久化 library.theme_color。
