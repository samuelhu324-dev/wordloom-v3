这页应该从“漂亮封面墙”升级成“这个 Library 的书架运营面板 + 漂亮封面”。
也就是：信息结构按照 Plan_13 + Chronicle 来走，视觉用你新书橱封面去包装。
我分 4 块说：要展示什么 → 页面结构 → 卡片长什么样 → 实现上怎么跟 Copilot 讲。

1. 这页到底要回答哪些问题？
结合 Plan_13 和你现在的 Chronicle / Book status，Bookshelves 页最好能让你一眼看到：


每个书架上“书的成熟度”


Books 总数


Seed / Growing / Stable / Legacy 各是多少




最近的活跃情况（Chronicle）


最近一次活动时间


7 天内编辑次数 / 7 天内浏览次数


一个“健康度”标记：Active / Slowing / Stale / Cold




管理需要的基础信息


书架名称、简介、类型（学习 / 翻译 / 归档……）


是否置顶（Pinned）、是否 Archive


入口按钮：进入该书架的 Books 列表




所以你可以把目标理解成：

“这里是 Library 内部的书架看板，而不是单纯的图片相册。”


2. 页面整体结构：三段式
以你现在 Screenshot1 为基础，把布局改成三部分：
(1) 顶部：Library 概览 + 控件


左：当前 Library 名称（或返回按钮）


中：进度条 + status 分布（整个 Library 维度）


已经有的「Seed/Growing/Stable/Legacy 统计卡」可以搬上来一排放着




右：操作控件


排序：最近更新 / 最多书 / 最多 Stable / 最活跃 / 最久没动


筛选：全部状态 / Active / Stale / Archived


视图切换：舒适（卡片） / 紧凑（列表）


新建书架按钮




(2) 中间：Pinned Shelves 区


标题：已固定书架


用两行或三行卡片展示 Pinned 的书架（重点展示）


(3) 下方：其他书架列表 / 分页


标题：其他书架 + 右边显示总数 10


根据当前视图模式显示为「卡片列表」或「紧凑列表」


底部分页 / “加载更多”



3. 每条书架怎么展示？（舒适卡片版）
结合 Plan_13 里“表格脑，别做 Excel 脸”的思路，建议一条卡片分成“封面 + 信息两块”：
3.1 卡片左上：书橱封面（你那张新图）


使用：书橱 PNG（透明背景） + 背后墙底色（--wall-color）


--wall-color 来自：


该书架自己的 themeColor（如果有）；否则


Library 的 themeColor 或根据封面图片提取主色（后面你再做）




尺寸：横向 16:9 左右，高度与现在的封面差不多


整个卡片 hover 时：


封面稍微放大 2–3% + 阴影加深一点


左侧有“把书架拉出来”的感觉




3.2 封面下方 / 右侧：信息区
信息区可以分两行：
第一行：标题栏


书架名称（大号字）


类型 tag：[学习] [翻译] [归档] 之类


状态标签：PINNED / ARCHIVED


右侧是一个 ⋯ 菜单（重命名 / 归档 / 删除）


第二行：指标栏（文字串起来，别画格子）
用一句“带点运营感”的句子把指标串起来，例如：

Books 12 · Seed 3 · Growing 5 · Stable 3 · Legacy 1 · ✏ 9 / 7d · 👁 21 / 7d · 🕒 Active

或者当行太长，可以断成两行：


行1：Books 12 · Seed 3 · Growing 5 · Stable 3 · Legacy 1


行2：✏ 9 / 7d · 👁 21 / 7d · 🕒 Active（last 2 days）


样式上：


每个数字前面有一个小 label 或 icon（Books / ✏ / 👁 / 🕒），方便扫视


颜色都尽量淡，只有异常状态（比如 Stale / Cold）用轻微橙色/灰色高亮


这块区域是 flex row，每段给一个 min-width 保证对齐，但不要画竖线


底部右侧：动作按钮


查看书籍（View Books）


可选：快速添加 Book 小按钮



4. 紧凑视图（Compact）：半表格模式
当用户在 View ▾ 里切换到紧凑模式时：


去掉大封面，只保留左侧一个小图标（圆形缩略的书橱 / Tag 颜色条）


每行高度减半


把所有指标压缩成一行：



StudyLog · Books 12 · Seed 3 / Grow 5 / Stable 3 / Legacy 1 · ✏ 9 /7d · 👁 21 /7d · 🕒 Active



可以用很淡的 zebra stripe 或列对齐，让“对比数字”更轻松，但仍然避免重格子线（保持不是 Excel）


这个模式主要给你自己做审计 / 排查用，普通用户一直停在舒适卡片视图就够了。

5. 实现上要跟 Copilot 说什么？
5.1 后端 / API：BookshelfSummary DTO
给 Copilot 一个清晰的数据模型，会非常好用，比如：
type BookStatus = 'seed' | 'growing' | 'stable' | 'legacy';

interface BookshelfSummary {
  id: string;
  name: string;
  description: string | null;
  kind: 'study' | 'translation' | 'archive' | 'misc';
  isPinned: boolean;
  isArchived: boolean;

  coverUrl: string | null;      // 将来如果有单独封面
  themeColor: string | null;    // 例如 "#e8d4b0"

  bookCounts: {
    total: number;
    seed: number;
    growing: number;
    stable: number;
    legacy: number;
  };

  editsLast7d: number;
  viewsLast7d: number;
  lastActivityAt: string | null;  // ISO datetime, 来自 Chronicle
  health: 'active' | 'slowing' | 'stale' | 'cold';
}

API：


GET /api/v1/libraries/{id}/bookshelves?sort=...&filter=...
返回一个 BookshelfSummary[] + totalCount。


Chronicle 这边只要保证能算出 editsLast7d / viewsLast7d / lastActivityAt / health 四个字段就够用了。
5.2 前端组件拆分
可以让 Copilot 帮你搭出下面几个组件：
// 顶部总结 + 控件
<BookshelfHeader
  library={librarySummary}
  filters={filters}
  onFiltersChange={...}
/>

// 主体列表
<BookshelfList
  viewMode={viewMode}         // 'comfortable' | 'compact'
  shelves={bookshelfSummaries}
/>

// 单个卡片（舒适模式）
<BookshelfCard shelf={shelf} />

// 紧凑模式的行
<BookshelfRow shelf={shelf} />

// 封面组件：透明书橱 + 动态墙色
<ShelfCover themeColor={shelf.themeColor ?? library.themeColor} />

ShelfCover 里面就用我们刚说的结构：
<div className="wall" style={{ '--wall-color': themeColor }}> + <img src="/img/shelf.png" />。

6. 小结一口气概括


信息结构：
Bookshelf 页从“封面墙”升级为“书架运营面板”：每个书架要带上
Book status 分布 + Chronicle 活跃度 + 健康度。


布局：
顶部是 Library 级的进度和控制条，下面分 Pinned 和 其他书架 两块，
每条用“卡片式行 + 封面 + 指标串”展示；
再提供一个紧凑视图做半表格模式。


视觉：
封面统一用你那张透明书橱 PNG，背后墙色由 CSS 变量控制，
将来可以根据封面主色 / themeColor 自动染色。


这套方案对 Copilot 来说也很好消化：一个新的 BookshelfSummary DTO + 一条新列表 API + 几个 React 组件，基本就能把你现在 Screenshot1 那页平滑重构过去。
