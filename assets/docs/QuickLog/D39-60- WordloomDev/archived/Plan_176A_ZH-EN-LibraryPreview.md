Plan: Library 页面中英文文案改造（Plan176A）
Status: ✅ Completed (2025-12-07)
范围：/admin/libraries 的 LibraryMainWidget、LibraryList、LibraryCard/LibraryCardHorizontal、LibraryForm、LibraryTagsRow 及其 toast/tooltips。
这个计划基于你当前的 Next.js + 自己的 i18n 实现（src/i18n），只做“怎么改”的规划，不直接动代码。

Steps
在多语言字典里新增 Libraries 相关文案 key

文件：src/i18n/locales/en.ts / src/i18n/locales/zh.ts
新增以下 key（按现有扁平命名风格）：
libraries.title
zh："书库"
en："Libraries"
libraries.subtitle
zh："你的所有知识空间。用书库把不同领域分开管理。"
en："All your knowledge spaces. Use libraries to organize different domains."
搜索框：
libraries.search.placeholder
zh："搜索书库…"
en："Search libraries…"
libraries.search.ariaLabel
zh："搜索书库"
en："Search libraries"
新建按钮：
libraries.new
zh："新建书库"
en："+ New Library"
排序下拉（截图 3，那四个选项）：
libraries.sort.lastActivity
zh："最新活动"
en："Latest activity"
libraries.sort.mostViewed
zh："浏览最多"
en："Most viewed"
libraries.sort.latestCreated
zh："最新创建"
en："Latest created"
libraries.sort.byName
zh："按名称排序"
en："Sort by name"
排序控件自身 aria-label：
libraries.sort.ariaLabel
zh："选择排序方式"
en："Choose sort order"
归档切换按钮：
libraries.archive.hide
zh："隐藏归档"
en："Hide archived"
libraries.archive.show
zh："显示归档"
en："Show archived"
视图切换（网格 / 列表，顺手一并整理）：
libraries.view.grid
zh："网格视图"
en："Grid view"
libraries.view.list
zh："列表视图"
en："List view"
在 Libraries 页面主组件里接入 useI18n

文件：src/widgets/library/LibrariesWidget.tsx
顶部引入：import { useI18n } from '@/i18n/useI18n';
组件内部调用：const { t } = useI18n();
把标题和副标题从写死文本改成 i18n

位置：同一个 LibrariesWidget 组件顶部 “Libraries / 你的所有知识空间…” 那一块。
改造方式：
标题：从写死 Libraries → 使用 t('libraries.title')
副标题：从中文句子 → 使用 t('libraries.subtitle')
搜索框输入框与按钮改成 i18n

搜索输入框：
placeholder="Search libraries…"  → placeholder={t('libraries.search.placeholder')}
aria-label="Search libraries" → aria-label={t('libraries.search.ariaLabel')}
右侧 + New Library 按钮：
文案 + New Library → {t('libraries.new')}
排序下拉选项和控件标签改成 i18n

位置：LibrariesWidget 里控制排序的下拉（你截图 3 那块）。
把现在的 SORT_OPTIONS 常量从纯中文字符串，改成“value + labelKey”的形式，例如：
{ value: 'last_activity', labelKey: 'libraries.sort.lastActivity' } 等。
渲染 option 时用：{t(option.labelKey)}。
下拉本身的 aria-label 设置为：aria-label={t('libraries.sort.ariaLabel')}。
归档显示/隐藏按钮改成 i18n

原来的逻辑是一个布尔值控制 “隐藏归档 / 显示归档”。
根据状态选择：
隐藏时：t('libraries.archive.hide')
显示时：t('libraries.archive.show')
这样按钮会随语言切换而变。
列表/网格视图切换的 aria-label 改成 i18n（顺手补全）

在网格 / 列表按钮上：
aria-label={t('libraries.view.grid')}
aria-label={t('libraries.view.list')}
Further Considerations
如果你希望“书库”统一叫 “Libraries / Library”，可以以后把其它页面（比如导航、Basement 提示文案）也统一使用 libraries.* 的这些 key。
这个计划只动 src/i18n/locales/*.ts 和 src/widgets/library/LibrariesWidget.tsx，比较集中、风险小，适合你一步一步实现并回归检查。
你实现完这一页后，我们可以按同样模式扩展到 Tags、Basement 等其他管理页面，逐步完成整个 Admin 区域的中英文切换。

## 2025-12-07 实施记录（Plan176A 状态）
- ✅ 语言包扩展：`libraries.list.* / libraries.card.* / libraries.cardHorizontal.* / libraries.form.* / libraries.tags.*` 等 key 已补齐，覆盖工具提示、对话框、按钮与无数据态。
- ✅ 组件接入 useI18n：`LibraryMainWidget`、`LibraryList`、`LibraryCard`、`LibraryCardHorizontal`、`LibraryForm`、`LibraryTagsRow` 全量改为从 `t()` 读取固定文案，包含 toast、aria-label、tooltip、对话框、校验信息。
- ✅ 日期/时间本地化：卡片与列表使用 locale 感知的 `formatRelative` / `formatAbsoluteDateTime` / `formatDate`，保证中英文环境时间描述一致。
- ✅ Tag 选择器回归：`LibraryForm` 的推荐状态、空提示、主题色校验等全部接入 i18n，并修复 `tagEmptyHint` 先引用后定义导致的运行时异常。
- ✅ Tags 列渲染：`LibraryTagsRow` 默认占位、`+N` tooltip、aria 描述全部接入翻译，实现列表/卡片之间一致的中英双语体验。
- ✅ 交付结论：Plan176A 所列 UI 均已切换到 useI18n，管理员看到的固定文案、日期提示与可访问文案都可随语言切换；后续页面可复用相同 key。

## Linked Documents
- VISUAL_RULES.yaml → `library_i18n_refresh` / `bookshelf_i18n_refresh` sections
- ADR-161 – Library Page Bilingual Refresh (Plan176A)
- ADR-162 – Bookshelf Dashboard Bilingual Refresh (Plan177A follow-up)