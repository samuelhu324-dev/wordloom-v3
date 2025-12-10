先给结论：你现在要的只是「中文计划（设计说明）」，还不需要我真正改代码。我下面会用中文，把 Plan 174A 的想法落成一份具体可执行的实现计划，并结合你现有 frontend、backend 结构和「把 Libraries 菜单改成 Language，下拉选择中/英」这个 UI 要求。

**状态（2025-12-06）**：✅ 已按照 `ADR-154-plan174-i18n.md` 执行，涉及 Rule 更新（DDD: POLICY-I18N-PLAN174A-UI-LANGUAGE / HEXAGONAL: i18n_runtime_strategy / VISUAL: navigation_language_switcher）。此文档现作为历史记录与变更追踪引用。

一、整体目标与范围

在 Wordloom Admin 前端实现 UI 级别的中/英切换：
支持两种语言：zh-CN（中文）/ en-US（英文）。
只翻译 UI 文案（导航、按钮、提示、错误信息等），不翻译业务数据（书名、块内容等）。
不改 URL 结构，不引入 /en、/zh 路由前缀。
语言首选项通过前端 localStorage 持久化，预留第二阶段与 /me/settings 后端接口同步。
顶部共用粘性菜单：
原来的 Libraries 菜单改为 Language，点击/hover 出现下拉菜单，风格和交互复用现有 Workbox 下拉菜单。
下拉项提供 中文 / English 两个选项，选中后全局 UI 切换语言。
二、后端 / Domain 侧（第一阶段可以只设计，不必立刻上线）

UserSettings 增加 uiLanguage 字段（设计）
目标：为未来「账号级」语言偏好预留字段，方便多端共享设置。
约定类型：
UiLanguage = 'zh-CN' | 'en-US'
建议位置（示意）：
backend/api/app/modules/user/domain/user_settings.py（实际文件名可按你现有 User/Profile 模块调整）。
领域模型设计（伪代码概念级）：
字段：ui_language: UiLanguage = 'zh-CN'
方法：set_ui_language(lang: UiLanguage)，只做枚举校验+赋值。
仓储与接口（第二阶段才实现）：
UserSettingsRepository 增加 ui_language 持久化。
API：GET /me/settings / PUT /me/settings 读写 ui_language。
第一阶段执行策略：
此字段可以只在 DDD_RULES / ADR 里「设计」、不改表结构；真正改 Schema & API 放到后续 i18n Phase 2。
三、前端 i18n 基础结构设计

在 src 下新增 i18n 子目录（可视为独立“横切模块”）：

目录结构（计划）：

frontend/src/i18n/
locales/
en-US.ts
zh-CN.ts
config.ts
I18nContext.tsx
useI18n.ts
LanguageSwitcher.tsx（纯逻辑组件，不直接耦合导航布局）
语言字典 locales/*.ts
en-US.ts（示例 key 设计）：

app.title, nav.libraries, nav.bookshelves, nav.basement
nav.language: "Language"
language.zhCN: "中文"
language.enUS: "English"
按模块前缀分类：nav.*, button.*, basement.*, editor.*, toast.* 等。
zh-CN.ts：

使用相同 key 集合，对应中文文案：
如 nav.libraries: '文库', nav.language: '语言', language.zhCN: '中文', language.enUS: 'English' 等。
约束：

不使用纯中文当 key；统一使用 模块.语义，为未来增加语言留余地。
所有 UI 新文案一律先加 key，再在组件里通过 t() 使用，禁止再写硬编码中/英文。
配置 config.ts
定义受支持语言、默认语言：
supportedLanguages = ['zh-CN', 'en-US'] as const
defaultLanguage: 'zh-CN'
暂不引入「自动检测浏览器语言」逻辑，后续可选。
I18nContext + I18nProvider
设计目标：

提供 (lang, t, setLang, messages) 的 React Context。
内部负责从 localStorage('wordloom.uiLanguage') 初始化语言。
setLang 时：
更新 React state
写回 localStorage
预留 TODO：未来调用 /api/me/settings 同步。
关键点：

t(key, vars?) 支持简单 {name} 变量替换。
t 未找到 key 时 fallback 为 key 字符串本身，以避免渲染报错。
useI18n Hook
简单封装 useContext(I18nContext)：
若未在 Provider 内使用则抛出清晰错误（方便调试）。
上层组件只通过这一个 Hook 访问多语言。
根布局挂 I18nProvider
在 layout.tsx 中：
用 I18nProvider 包裹整棵树：
<body><I18nProvider>{children}</I18nProvider></body>
第一阶段 <html lang="zh-CN"> 可以暂时写死，第二阶段再根据当前 lang 注入。
四、导航栏改造：Language 菜单 + 下拉切换

定位共用粘性菜单组件
依据 TREE.md，顶层布局可能在：
layout.tsx 或
某个共享导航组件（例如 frontend/src/shared/layouts/AdminShell.tsx / Header.tsx）。
计划步骤（代码执行阶段用）：
用搜索工具定位 Libraries 文案：
找到负责主导航的 React 组件。
确认 Workbox 下拉菜单的实现（样式 / 动画 / 交互），准备复用那一套菜单组件或 primitives。
把 Libraries 菜单改成 Language 菜单
原有结构（推断）：
顶部导航中可能有 <Link href="/admin/libraries">Libraries</Link> 或对应中文文案。
目标改造：
该位置改为一个 Language 入口：
标签文字来自 t('nav.language')。
交互方式完全复用 Workbox 的 hover/点击展开模式（共用 Menu 组件）。
下拉内容：
两个菜单项：
中文（t('language.zhCN')）
English（t('language.enUS')）
当前选中的语言项可显示勾选或高亮；aria-checked/aria-pressed 同步。
LanguageSwitcher 与导航集成
设计思路：
LanguageSwitcher.tsx 只包含语言切换逻辑（使用 useI18n）。
导航组件内，使用现有的 Dropdown/Menu shell，把 LanguageSwitcher 嵌进去作为 menuItems 渲染源，样式与 Workbox 完全一致。
行为要求：
选择语言后：
调用 setLang('zh-CN'|'en-US')。
不刷新整页，依赖 React Context 即时触发所有使用 t() 的组件重渲染。
UI 反馈：
当前语言高亮 / 打勾。
菜单自动关闭。
五、逐步替换现有 UI 文案

扫描和归类文案
使用代码搜索：
中文："文库", "书架", "地窖", "保存", "取消", "删除" 等常见 UI 文案。
英文："Libraries", "Bookshelves", "Basement", "Save", "Cancel", "Delete", "Restore" 等。
按模块归类：
导航：nav.*
按钮：button.*
Toast / 错误提示：toast.*, error.*
Basement 视图：basement.*
Book/Bookshelf/Library 特定页面：library.*, bookshelf.*, book.* 等。
为每一类文案定义 key
例如：
顶部导航：
nav.language, nav.workbox, nav.libraries, nav.bookshelves, nav.basement…
顶部操作按钮：
button.save, button.cancel, button.delete, button.restore, button.close…
Basement 空态与提示：
basement.empty, basement.noDeletedBooks, basement.noLibraries 等。
将 key–文案添加到 en-US.ts 与 zh-CN.ts。
组件中接入 useI18n & t()
对已识别出的组件：
引入 useI18n。
const { t } = useI18n();
把硬编码文案替换为 t('对应key')。
注意：
不要在 Domain/Store/后端 DTO 层塞入翻译后的字符串；
所有翻译都在 UI 组件中完成。
六、与后端用户设置同步（第二阶段）

启动时拉取 /me/settings（如果存在）
在 I18nProvider 的初始化 effect 内：
若 localStorage 中无语言设置：
调用经封装的 API Client 请求 /api/me/settings 或 /me/settings。
若返回 ui_language 字段且值在 supportedLanguages 内，则用它初始化 lang，同时写入 localStorage。
切换语言时同步到后端
在 setLang(next) 内追加（第二阶段再做）：
调用现有 api client：PUT /api/me/settings { uiLanguage: next }。
将出错处理（网络失败等）做成“软失败”：前端照样更新本地语言，但在日志中打印/上报错误。
规则
前端永远以本地 I18nContext 为最终渲染依据；
后端设置只是「默认值来源 + 多端同步」；不反向强制刷新当前页面语言。
七、验证与回归计划

前端单元测试（Vitest）
为 I18nContext / useI18n 编写测试：

默认语言= defaultLanguage。
有 localStorage('wordloom.uiLanguage') 时优先使用该值。
setLang 更新 state & 写入 localStorage。
t('unknown.key') 返回 key 文本自身或明确 fallback。
为 LanguageSwitcher / 导航集成写测试：

初始状态下，当前语言按钮 aria-pressed=true。
点击另一个语言按钮时：
setLang 被调用。
文本渲染跟着变（可以通过 mock 字典或 snapshot 断言）。
端到端行为（Playwright 或手动 checklist）
手动（最小）Checklist：
打开 Admin 页面，默认看到中文 UI（或 defaultLanguage 配置的语言）。
打开粘性菜单 → Language 下拉，切换到 EN：
导航文案、按钮文案变为英文。
刷新后仍保持英文（localStorage 生效）。
切回中文，观察相同行为。
在 Basement / Book / Bookshelf 等关键页面，确认空态/Toast/按钮都随着语言改变。
八、执行顺序建议（给未来实现用）

搭建 src/i18n 基础结构：config.ts、locales、I18nContext、useI18n、LanguageSwitcher。
在 app/layout.tsx 中挂 I18nProvider。
找到顶栏导航组件：
把 Libraries 改成 Language 菜单；
复用 Workbox 下拉样式，接入 LanguageSwitcher。
选取 1–2 个代表性页面（如 /admin/libraries 导航栏、Basement 页面、一个对话框）：
把可见文案全部换成 t()。
作为 i18n「试点」。
补充单测和简单的手动回归。
视情况分批把其余模块的文案迁移到字典。
如果你愿意，下一步我可以按这个计划，直接在 src 里帮你搭好 i18n/ 目录和 Provider 骨架，并在导航里实际接好 Language 下拉菜单，然后再逐步抽取一批关键文案到字典里。