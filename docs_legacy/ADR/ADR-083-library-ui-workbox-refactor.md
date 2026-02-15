# ADR-083: Library UI Workbox Refactor

Date: 2025-11-21
Status: Accepted
Authors: Frontend / Architecture
Related: ADR-082, VISUAL_RULES v2.6, DDD_RULES v3.10, HEXAGONAL_RULES v1.9
Supersedes: (None) – Evolves visual integration from POLICY-014

## Context
现有 /admin/libraries 页面存在以下体验与结构问题：
1. Basement 以巨大蓝色卡片混在普通 Library 卡片中，视觉层级混乱，难以区分“知识空间”与“系统工具”。
2. 视图模式命名 vertical/horizontal，不符合业界 Grid/List 常规心智；无副说明与搜索，缺少“控制台”入口感。
3. 卡片样式使用局部写死颜色与不统一的圆角 / 阴影，难以扩展主题；tokens 已有 --color-* 体系但未完全应用。
4. Basement inline 切换逻辑（showBasement）增加不必要的状态分支；回收站访问与主列表交织。
5. 缺少高密度列表视图，无法快速纵览与批量管理；空状态提示过于简单。

## Forces / Drivers
- 清晰信息架构：将系统工具与内容空间分离，降低认知负荷。
- 早期 SaaS 控制台观感：Hero Row 提供操作与上下文化说明。
- 主题可扩展：统一使用 tokens.css 变量，为后续多主题与动态主题切换奠定基础。
- 降低维护复杂度：移除 Basement 内嵌状态分支，菜单导航即职责分离。
- 渐进增强：先前端搜索过滤；后端搜索与活跃度指标稍后迭代，不阻塞当前 UI 改进。

## Decision
实施 Library UI Workbox 重构：
- Header 新增 "⚙ Workbox" 下拉菜单：Basement / Chronicle / Stats / Settings；后续 DevTools/Toolkit 统一挂载。
- /admin/libraries 页面：移除 inline Basement；Hero Row = 标题 + 副说明 + 搜索框 + Grid/List 切换 + 创建按钮 + 回收站文字入口。
- 视图模式标准化：仅保留 grid 与 list；弃用 vertical/horizontal；localStorage 键改为 `wl_libraries_view`。
- List 视图：行高 ~48px，列：名称 / 说明 / #Books(预留) / 创建时间；行 hover 背景提升，无额外复杂操作菜单暂留。
- Grid 卡片：统一圆角 var(--radius-lg)，hover 阴影从 shadow-sm 升级 shadow-md + 微移位 (translateY -2px)。
- 颜色 / 阴影 / 间距全部使用 tokens；新增兼容别名 --bg-secondary / --border-color，避免旧代码瞬时崩溃，后续迁移后删除。
- 搜索：前端过滤 name + description；未来后端支持后切换 query 方式。
- Basement 链接：通过 Workbox 菜单或 Hero Row “查看回收站”按钮进入 /admin/basement，不再注入主列表。

## Implementation Summary
Frontend:
- 修改 header.tsx + Header.module.css：添加 Workbox 下拉及样式。
- 重写 LibraryMainWidget：集成搜索、Grid/List、回收站入口、移除 Basement 卡片。
- 重构 LibraryList：viewMode(grid/list) + 前端搜索过滤 + List 行布局；移除 extraFirst。
- 更新 Card.module.css 使用统一 tokens；tokens.css 添加兼容别名。
- 新增/更新规约：VISUAL_RULES.yaml、DDD_RULES.yaml、HEXAGONAL_RULES.yaml 添加与此次决策相关条目。
Documentation:
- 本 ADR 记录决策；DDD_RULES 新增 POLICY-LIBRARY-UI-WORKBOX-REFACTOR；VISUAL_RULES 加入视觉与交互细则；HEXAGONAL_RULES 增 UI 集成指引。
Backend:
- 无端口修改；继续单用户模式；后续搜索/统计为独立 ADR。

## Alternatives Considered
1. 保留 Basement 卡片但缩小尺寸：仍混淆角色，无法彻底分离信息架构。
2. 将系统菜单放 Sidebar：现阶段采用 Header-only 导航策略；侧边栏增加结构噪音。
3. 直接实现后端搜索再重构：增加等待时间；前端过滤成本低，适合迭代式交付。

## Consequences
Positive:
- 视觉与交互更接近主流 SaaS 控制台；认知负荷降低。
- 主题扩展准备完成；后续深色 / Loom Dark 一致性更高。
- 代码复杂度下降：移除 showBasement 分支与 extraFirst 注入。
- 清晰扩展点：Stats/Chronicle 指标可在后续阶段自然接入。
Trade-offs:
- 临时失去 Basement 卡片快速“视觉提醒”；通过 Hero Row 文本与菜单弥补。
- List 视图当前不含批量操作；未来需在行尾加入操作菜单或多选机制。

## Rollback Plan
若用户反馈强烈需要 Inline Basement：
1. 在 LibraryMainWidget 恢复 extraFirst 区域但使用简化灰色提示块，而非大型卡片。
2. 保留 Workbox 菜单，不回退结构分离。

## Future Work
- 接入后端搜索：`GET /libraries?query=`。
- 活跃度指标：最近 7 天更新数 / 阅读时长（Stats 模块落地后）在卡片底部透出。
- 批量操作：List 视图添加多选 + 行操作菜单。
- Menu 分组：Workbox 项目超过 6 个后按“数据 / 系统 / 工具”分组。

## Status Links
- VISUAL_RULES: navigation_policy.workbox_menu, component_styles.library_ui_refactor
- DDD_RULES: POLICY-LIBRARY-UI-WORKBOX-REFACTOR
- HEXAGONAL_RULES: ui_integration_guidelines.library_workbox_refactor

## References
- ADR-082 单用户模式支撑列表不需要 user_id 过滤
- Industry patterns: Notion / Linear / Figma console layout conventions
- Initial Plan: Plan_7_LibraryUI.md

## Decision Record
Accepted 2025-11-21. Active until enhanced Stats + Search shipped.
