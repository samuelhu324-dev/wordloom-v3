> 备注：早期草稿中的 FROZEN 状态已统一命名为 ARCHIVED。

1. 书橱列表的排序规则怎么定？
建议：先用规则排序，不搞「神秘移动」

默认排序：最近活动（Recommended）

关键字段可以是：

last_activity_at：最近一次 Book / Block 的编辑时间

没有活动时 fallback 到 updated_at / created_at

用户感知：

最近动过的书橱在最上面 → “现在在用什么，一眼看见”。

归档 / 复位时的行为：

书橱有状态：ACTIVE / ARCHIVED

列表视图建议这样：

按状态分区 + 统一排序：

上面：ACTIVE 区（默认展开）

下面：ARCHIVED 区（可折叠）

每个区内都按「最近活动」排序

这样归档时：书橱从 ACTIVE 区消失 → 跑到 ARCHIVED 区顶部（因为刚刚状态变更，updated_at 更新了）
复位时：回到 ACTIVE 区，同样在 ACTIVE 区靠前。

如果你暂时不想做「分区」，也可以：

默认过滤：状态 = ACTIVE

想看归档书橱时，筛选下拉选 ARCHIVED

排序逻辑仍然是「最近活动」

这种实现成本最低，而且符合审计 / 后台系统常见做法。

简单总结：
不要让归档/复位偷偷改变「自定义顺序」；它只应该改变状态字段，排序依然靠活动时间来决定。

2. 要不要支持拖拽式排序？
TL;DR：先不要做拖拽排序，只保留规则排序；以后最多在「少量对象」的场景再加拖拽。
为什么大多数「审计 / 知识库 / 看板」不默认让你拖来拖去？

可解释性

按规则排序（名字 / 时间 / 数量） → 你一看就知道为啥排在这。

自定义拖拽排序 → 过一阵你忘了自己当时怎么拖的，只剩下“这列表很乱”的感觉。

实现成本高

要存「position」字段 + 读写逻辑 + 乐观更新

还要考虑分页场景拖拽、权限、多用户同时拖拽等问题。

你现在更需要把 Wordloom 的业务流打通，而不是在这儿熬 UI 小糖浆。

Wordloom 的语义里，书橱不是 Trello 卡片

对你来说，一个 Library 里可能几十个 Bookshelf。

它们更像“报表”、“业务子域”，而不是“手动排序的待办”。

可以考虑的轻量变体（以后再说）：

只允许拖拽 Pinned 书橱的顺序

类似浏览器书签栏：Pinned 区域不多，用户会更在意精细排序。

全部书橱列表仍然遵从规则排序（最近活动 / 名称）。

在你当前这个阶段，我会建议：

只实现下拉筛选 + 排序选项：

排序：最近活动 / 名称（A–Z）/ 创建时间 / 书本数

视图永远看起来规整，不引入自定义顺序。

3. 标签（Tags）的顺序怎么排？

你现在每个 Bookshelf 最多 3 个标签，这个数量非常可控，所以顺序只要：

全局上（tag 列表页 / 下拉搜索）：

默认按名称字母顺序（推荐）

英文：A–Z

中文：可以用拼音排序，或者保留插入顺序（取决于以后是否大量使用中文 tag）

原因：最可预期，最方便查找；行业里很多系统（Jira 标签、GitHub labels）都是这么做。

可选：按使用频率排序

比如“最近使用”优先显示在搜索框下方建议里。

但是数据库 + 统计就多一步，当前阶段可以先不做。

在每个 Bookshelf 卡片上：

建议 按「tag 类型优先级」+ 名称排序：

比如：领域 / 所属模块类 tag 在前面，状态类 tag 在后面。

如果你没有设定优先级，就简单按名称排序即可。

UX 角度：
Bookshelf 卡片上的 tag 更多是“快速扫一眼辨认”，所以“始终一个稳定的顺序”比“你能自定义顺序”更重要。

4. 帮你把这三个问题连起来总结一下
书橱排序：建议这样落地

列表页：

顶部控件：

排序：最近动态 / 名称 / 创建时间 / 书本总数

筛选：全部 / ACTIVE / ARCHIVED

默认：

排序：最近动态

过滤：只看 ACTIVE

数据字段：

status：ACTIVE / ARCHIVED

last_activity_at

created_at

books_count

行为：

归档 → status = ARCHIVED，updated_at & last_activity_at 刷新 →

在“全部 + 最近动态”视图里，它会被排到 ARCHIVED 区的靠前位置 / 或者只在 ARCHIVED 筛选中可见；

复位 → status = ACTIVE，同理进入 ACTIVE 区前排。

拖拽：先不做

不实现全列表拖拽。

未来如果你觉得 pinned 区真的需要人工排序，再加一个 sort_order 字段，只对 pinned subset 生效。

标签顺序：

全局：按名称排序（A–Z / 拼音），可选“最近使用”增强。

卡片：最多 3 个 tag，依旧按名称排序或轻微按类型分组。

重点是：顺序稳定，让你在 LibraryLog 里扫一眼就能认出是哪类书橱。

Very short English recap

Bookshelf ordering

Default sort by last_activity_at (recent activity).

Filter by status: ACTIVE vs ARCHIVED.

Archiving/unfreezing only changes status (and timestamps), the order is still rule-based.

Drag & drop

Don’t implement global drag sorting now.

Maybe later only for a small “Pinned” area if you really need manual ordering.

Tag ordering

Globally: alphabetical order (A–Z / pinyin).

On each bookshelf: same order, max 3 tags → easily scannable.

Stable, predictable ordering beats custom ordering for an audit-style system.

你现在这一整套 Library → Bookshelf → Book 的 UI 气质已经很统一、很“审计后台”了。
接下来在排序 / 标签这些地方守住“可解释 + 可预期”的原则，就会越来越像一套真正能被别人拿来审项目的工具，而不是一块随意摆放的桌面。

////////////////////////////////////////////////////////////////////////////

你可以在 Chronicle 里按书架计算「最近活动天数」，用事件比如：

BookCreated / BookUpdated

BlockAdded / BlockEdited / BlockStatusChanged

BookshelfViewed（浏览也算轻活动）

设 days_since_last_activity = 距离最后一条事件的天数。
然后给每个书架打一个“温度状态”：

ACTIVE / 活跃:         0–7 天内有活动
减速 / Slowing:       8–21 天无活动
趋冷 / Cooling:      22–60 天无活动

这样：

头部卡片里的 “趋冷” 数字 = 状态为 Cooling 的书架个数

“减速” = Slowing 数量

“归档” = Archived 数量

“活跃” = Active 数量

你之后如果想更精细，可以把“活动”换成「最近 7 天事件数 vs 最近 30 天事件数的跌幅」，但第一版用「距离最后一次活动的天数」已经足够审计风 + 好实现。

---

## Progress 2025-11-25

- [x] `/api/v1/tags/catalog` 500 已修复：DIContainerReal 暴露 `get_list_tags_use_case`，ListTags adapter 连到真实仓库，Tag Catalog 前端恢复可用。
- [x] Bookshelf Dashboard UI 调整：恢复 PIN 徽标丝绸蓝浅底、标签列加宽同时保持按名称排序，卡片标签最多 3 个时保持字母序。
- [x] 后端 `UpdateBookshelfRequest` 支持 `is_pinned`，快速置顶/取消置顶操作现在会立即返回正确状态。
- [ ] Duplicated tag 提示 & toast：待验证 catalog 列表后继续。