高层计划

调整 bookshelf 页面整体背景和卡片，让粘性菜单栏下方区域与 Libraries 页一致（灰色背景 + 白色卡片）。
复用 Libraries 页的头部结构：标题（丝绸蓝）、描述、分割线，套在 BookshelfDashboardBoard 外。
修正「活跃 / 减速 / 趋冷 / 归档」统计逻辑，确保和下方书橱真实状态一致。
所有颜色继续通过现有 CSS 变量 / theme tokens 走，不写死颜色值。
输出一份中文实施计划书，便于后续跟踪和 review。
(1) 粘性菜单栏下方背景 + 书橱卡片容器

目标：

Library detail（截图2）下方区域背景改为和 Libraries 列表页一样的灰感 app 背景。
每一条书橱行用一个白色卡片承载，类似 Libraries 列表页单条 Library。
具体改动建议：

在 page.module.css 中：
目前 .container 是纯白背景（继承 body），可以新增一个 .page 类（与 page.module.css 对齐），例如：
background-color: var(--color-bg-app);
适当加入现有 radial 渐变 token（如果在别处已有）或只用 --color-bg-app。
或者在 .container 外新增一层 .page 容器（如果已有就直接复用），保证 Library detail 与 Libraries list 统一用 --color-bg-app。
在 page.tsx 里：
最外层由 <div className={styles.container}> 改为：
<main className={styles.page}>
内部包一层 <div className={styles.container}>，与 LibrariesPage 相同结构。
书橱列表卡片：当前 BookshelfDashboardBoard 中 .row 已经是白底 + 边框：
background: var(--color-surface, #fff);
box-shadow 在 hover 时有轻微描边。
为了更像「卡片」，可以：
在 .table 外层（比如 .content 或 .wrapper）增加一个 background: var(--color-bg-secondary) / var(--color-bg-muted) 的区域，
或者在 .row 上增加一定圆角 border-radius: 12px; 并使用 gap 让卡片之间留出一点灰色背景。
关键是让 BookshelfDashboardBoard 所在的 dashboardSection 背景不是纯白，而是 var(--color-bg-app) 或 var(--color-bg-muted)，白色卡片通过 var(--color-surface) 搭出来，这样就和截图1的 Library 卡片气质统一。
(2) Bookshelf 界面复用 Libraries 头部结构

目标：
「书库列表」标题用丝绸蓝（通过 token 而不是硬编码色值）。
LibraryLog 下显示当前 Library 的 description。
标题/描述下加一条灰色分割线，与 Libraries 页视觉一致。
实现思路：
直接复用 page.module.css 里的 .header, .titleBlock, .description 样式（已经存在）：
在 page.tsx 里，你已经有：
<header className={styles.header}>
包含 <h1> + description + page actions。
这里需要做的是，将「LibraryLog 这条 detail 页」上的大标题仍然是 Library 名称，但在 Bookshelf dashboard 的 sticky 菜单下面，再加一块「书库列表」的小标题行。
一种不打乱结构的方式：
保留当前顶层 <header>（显示 Library 名 / 描述），这是和 Libraries 页一致的「库级」信息。
在 <section className={styles.dashboardSection}> 之前，插入一个新的块：
<section className={styles.subHeaderSection}>
  <div className={styles.subTitleBlock}>
    <h2 className={styles.subTitle}>书库列表</h2>
    <p className={styles.subDescription}>
      {library?.description || cachedLibrary?.description || '—'}
    </p>
  </div>
  <div className={styles.subDivider} />
</section>
在对应 CSS（同一个 page.module.css）中新增：
subTitle 颜色使用 token，例如：
color: var(--color-primary, var(--wl-silk-blue, #2563eb));
不要直接写 #2563eb，而是在你已有的 theme token 中选「丝绸蓝」，比如项目中常用的 --color-primary 或 --wl-brand-primary。
subDivider 使用与 Libraries 页分割线一致的颜色：
background: var(--color-border-subtle); 或 var(--color-border, #e2e8f0)。
高度 1px，宽度 100%，margin 顶底若干 var(--spacing-md)。
内容和组件复用：
为防止重复代码，你也可以抽一个小组件（例如 LibrarySectionHeader）放在 widgets/library 里，被 Libraries list page 和 Bookshelf dashboard page共同调用，但这不是硬性要求；当前阶段可以先保持 CSS 约定一致，后续再做抽象。
(3) 统计「活跃 / 归档」规则修正

你提到「现在归档显示为 8，可是下面书橱都是 ACTIVE 字段」，这说明：

统计目前基于「距最近活动天数」+ Archived override；
你现在希望：如果列表中所有书橱的 status 都是 ACTIVE，就计入「活跃」；如果 status 是 ARCHIVED 则归档；也就是统计要看「状态」，而不是仅看时间。
结合你之前 Plan_55 中的设定，我们可以这样修正：

保留基于 last_activity_at 的 ACTIVE / SLOWING / COOLING 划分规则，但对「归档数字」专门用 Bookshelf.status == ARCHIVED 来统计。
也就是说：
active/slowing/cooling 只计算 status == ACTIVE 的书架；
archived 只计算 status == ARCHIVED 的书架（与天数无关）。
这会让你在截图那种情况下（bottom 只有 ACTIVE）时：
活跃 / 减速 / 趋冷 会基于活动时间分布；
归档会是 0（因为没有 ARCHIVED）。
后端实现上，可以调整我们新加的 BookshelfHealthCounts 计算逻辑：

遍历 shelves 时：
如果 model.status == ARCHIVED：
archived += 1，health 字段可以仍然标记为 'archived'。
如果 model.status == ACTIVE：
根据 days_since_last_activity 分配到 active/slowing/cooling。
前端统计已经从后端 snapshot 里读取，不需要再额外改逻辑，只要后端按上述规则输出即可。

如果你更希望「活跃」也只基于状态，不看天数（即：只分 ACTIVE vs ARCHIVED），那也可以进一步简化：

health.active = count(status == ACTIVE)
health.archived = count(status == ARCHIVED)
slowing / cooling 可以暂时为 0 或通过其他逻辑填充。
看你更倾向哪一种，我可以再按你选择的版本微调后端逻辑。
(4) 颜色全部做 token 映射

当前样式已经大量使用 token：
var(--color-bg-app), var(--color-bg-secondary), var(--color-text-primary) 等。
按你的要求，后续调整会遵循：
所有新加颜色都写成 var(--xxx)，优先使用现有的：
主品牌蓝：--color-primary 或项目内定义的 --wl-silk-blue（如果存在）；
次级背景灰：--color-bg-secondary, --color-bg-muted, --color-surface;
分割线：--color-border, --color-border-subtle;
提示文案：--color-text-secondary, --color-text-tertiary。
如果你有专门的 Silk Blue token 名称（比如 --wl-silk-primary），可以告诉我；否则我会用 --color-primary + 注释标记它是丝绸蓝。
(5) 中文计划书（可靠可执行）

阶段 1：视觉结构统一

统一页面背景结构

在 page.module.css 中新增 .page 类，使用 var(--color-bg-app) 作为整体背景；
调整 page.tsx 最外层结构为 <main className={styles.page}><div className={styles.container}>…</div></main>，对齐 LibrariesPage。
确保粘性菜单栏下面看到的是灰色 app 背景，而不是纯白。
书橱列表卡片视觉

在 BookshelfDashboardBoard.module.css 中：
适当增大 .row 的圆角（例如 10–12px），保留 background: var(--color-surface)、border-bottom: 1px solid var(--color-border)；
使用 gap 或 margin-bottom 在相邻 .row 之间留出 app 背景（灰色）透出，形成独立卡片感；
如有需要，为整个 table 外层区域设置 background: var(--color-bg-secondary) + padding，以便区分内容区和 app 背景。
复用 Libraries 头部结构

在 page.tsx 的 dashboardSection 前，新加一个 subHeaderSection：
左侧 h2 文本为「书库列表」，右侧可暂不放按钮；
下方插入 div 分割线。
在 page.module.css 中新增：
.subHeaderSection（布局：flex + space-between）；
.subTitle 使用丝绸蓝 token：color: var(--color-primary)；
.subDescription 复用 .description 样式或略小的字体；
.subDivider 使用 background: var(--color-border-subtle) 的 1px 直线。
subDescription 的内容绑定 library?.description || cachedLibrary?.description，与顶部描述保持一致或再写一段更偏 bookshelf 的引导文案。
阶段 2：健康度 / 归档统计规则修正

确认业务规则

以 Plan_55 为基线，将需求拆分为两层：
UI 展示的 label：活跃 / 减速 / 趋冷 / 归档。
计数规则：
archived 数字只看 Bookshelf.status == ARCHIVED；
其他三个 bucket 只在 status == ACTIVE 的子集中按天数分配。
后端 UseCase 调整

在 GetBookshelfDashboardUseCase 中：
遍历 shelves 时：
如果 model.status == BookshelfStatus.ARCHIVED.value：
health = 'archived'，health_counts.archived += 1；
否则计算 days_since_last_activity，使用 0–7 / 8–21 / 22–60 划分为 active / slowing / cooling，相应累加。
保持 BookshelfDashboardItem.health 字段同步上述结果，前端可以继续根据单项 health 渲染。
前端 snapshot 消费

fetchBookshelfDashboard 已经读取后端的 snapshot；
BookshelfDashboardBoard 通过 data.snapshot 把 total / pinned / health 传给 onSnapshotChange；
page.tsx 中的 summary badge 显示：
活跃 = snapshot.health.active
减速 = snapshot.health.slowing
趋冷 = snapshot.health.cooling
归档 = snapshot.health.archived。
调整完成后，用一个测试 Library 验证：
当所有书橱是 ACTIVE 时，归档 = 0；
手动把某书橱设为 ARCHIVED 后，归档计数即时 +1。
阶段 3：设计与主题 token 打通

颜色 token 审核与修复

全文搜索 BookshelfDashboardBoard.module.css、page.module.css：
替换掉任何硬编码色值（如 #2563eb, #e5e7eb）为对应 token：
主蓝：var(--color-primary)；
背景：var(--color-bg-app), var(--color-bg-secondary), var(--color-surface)；
文本：var(--color-text-primary/secondary/tertiary)；
分割线：var(--color-border-subtle)。
对新加的 .subTitle / .subDivider 等都使用这些 token，避免裸色值。
交互与滚动体验

确保粘性菜单栏（排序 / 筛选部分）的底色与 dashboardSection 背景过渡自然：
若菜单栏使用白色，则下方灰色区域通过圆角 / 阴影与之分隔；
滚动时看起来像一块卡片内有表格，而不是「白色悬浮在灰背景上却没有容器」。
手动验证：
在一个 Library 下新建/归档多个书橱，观察 summary 各 bucket 数字与下方列表的 status、最近活动情况是否一致；
切换 Theme（如果有深浅色），确保新加的 token 配色在两种主题下都合理。