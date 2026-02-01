先列出高质量分步骤中文计划（含规则文件与前端改造），以便你确认后再进入执行。

Created 16 todos

下面是详细执行计划（已拆分为可操作步骤），供你确认后进入实施阶段：

总体目标

将 Bookshelf Dashboard 横排视图全面对齐 Library 列表的交互与审计风格：列结构、操作能力、主题与徽章、规则文件与 ADR 归档。
规则文件更新

VISUAL_RULES.yaml: 增加 bookshelf_dashboard_layout_v2 节，定义新列顺序(封面|名称|标签|成熟度|指标|操作)、Pinned 丝绸蓝主题变量(--wl-pinned-accent-*), 操作列按钮语义、A11y 说明、性能与禁止后端颜色写入。
DDD_RULES.yaml: 新增 POLICY-BOOKSHELF-DASHBOARD-LAYOUT-V2，明确：列布局属展示层；Pinned 顺序仍用 pinned_order；不新增书橱颜色字段；动作仅调用现有聚合命令；删除/归档不改变领域模型。
HEXAGONAL_RULES.yaml: 新增 bookshelf_dashboard_ui_port_v2 描述：无新增 Domain Port；使用既有 Repository + 应用服务；主题变量在 UI Adapter 注入；禁止跨聚合颜色写入。
ADR-096 文档

路径: assets/docs/ADR/ADR-096-bookshelf-dashboard-layout-v2-and-action-column.md
结构: Title, Status(Adopted), Context(对齐 Library 横排 + 降低认知跳转), Problem(信息密度低+缺操作), Decision(六列布局+操作列+Pinned 丝绸蓝徽章/按钮), Details(列定义/令牌/交互流/可访问性), Alternatives(保留旧紧凑+弹出菜单), Consequences(信息密度提升/实现复杂度↑), Rollback(保留旧组件分支 tag), References(ADR-094/095/087/082).
前端实现要点

Grid 模板：grid-template-columns: var(--library-avatar-size) 200px 180px 190px 150px auto;
拆分列：cellCover, cellName, cellTags, cellMaturity, cellMetrics, cellActions.
封面：用 libraryCoverMediaId 的 thumb；缺失回退到渐变+首字母。
名称列：Pinned/Archived 徽章 + 名称；移除 ACTIVE 文本。
标签列：多行 pill；最多显示前 N（后续 hover 展开）。
成熟度列：Seed/Growing/Stable/Legacy 四枚计数，aria-label “Seed 3 本”。
指标列：总书籍、7日编辑、7日浏览；数字为 0 时仍显示(稀疏数据可预期)。
操作列：编辑(Edit3)、置顶/取消置顶(Pinned Toggle)、归档/恢复、删除；Pinned 按钮用丝绸蓝主色（新 token）；所有按钮加 aria-label。
移除 statusLabel；逻辑归档→显示 Archived 徽章，Pinned 不与 Archived 共存（归档取消置顶）。
Mutation：使用 React Query useMutation；成功后 invalidateQueries(['bookshelves_dashboard', libraryId])；Pin/Unpin 乐观更新本地缓存。
Token 映射：在 tokens.css 添加
--wl-pinned-accent-bg
--wl-pinned-accent-text
暗色模式对应 --wl-pinned-accent-bg-dark / --wl-pinned-accent-text-dark
可访问性：操作按钮使用 aria-pressed（Pinned），删除二次确认用 aria-describedby 绑定隐藏描述。
测试策略

单元测试：pin→unpin 状态切换；归档后 pinned 自动移除；删除后列表数量更新。
Snapshot：空列表、有标签多行、成熟度非零、操作列渲染。
可访问性：检查 aria-label 存在；Pinned 切换触发 pressed 状态。
性能与回退

仅在初次挂载计算封面 URL；不引入复杂记忆除非性能瓶颈。
保留旧紧凑视图组件文件在 archived/ 目录以便快速 rollback（ADR 写明）。
变更记录

提升 VISUAL_RULES 版本号→2.8；DDD_RULES→3.11；HEXAGONAL_RULES→2.0。
DevLog / Changelog 添加“Bookshelf Dashboard Layout V2 + Actions Column”条目。
如果没有补充需求，我会按上述 TODO 顺序开始：先写三 RULES 文件补丁与 ADR，再进行前端组件与样式改造。需要我直接进入实施吗？你可以确认或调整后让我继续。