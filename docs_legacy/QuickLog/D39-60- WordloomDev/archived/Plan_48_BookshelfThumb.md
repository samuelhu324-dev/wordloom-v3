发生了什么？ / What’s happening

你现在的行为大概是这样的：

列表页 / LibraryLog → Bookshelf 列表

首次打开：前端从 API 拿到的数据里，bookshelf.cover_url 还是“旧图”（或者默认占位图）。

你在前端把「library 的封面 url」传给了某个 bookshelf Card 组件，用来显示缩略图。

这一步多半只是：

const cover = bookshelf.coverUrl ?? library.coverUrl;


或者是你在页面里 setState/props 临时覆盖了 coverUrl。

点进去某个书架详情

在详情页你直接拿 library.cover_url 做 header 背景，所以看起来“是对的”。

刷新页面（F5 / 重新进入列表）

页面重新请求 /api/v1/bookshelves 或类似接口。

后端返回的数据里，cover_url 还是旧值（你从来没改过 DB）。

前端列表组件按照接口字段渲染 → 于是又显示成“回滚图”。

所以这不是浏览器“记不住”，而是后端从来没记住这个新缩略图，你只是临时在内存里「贴了一张图」。

为什么详情页看着没问题？

因为你在详情页用的是「library 的封面」，跟 bookshelf 实体本身无关：

列表页：用的是 bookshelf.cover_url（或 fallback）。

详情页：可能是 library.cover_url 或 GET /bookshelf/:id 时顺便 join 了 library。

两边读的是不同字段 / 不同来源，所以显示不一致是正常现象。

怎么改才不会回滚？ / How to fix

你有两条路线可以选（从领域设计的角度我也顺便帮你排一下）：

方案 A：Bookshelf 不自己存封面，只“引用” Library 的封面（推荐）

逻辑：

领域规则：书架从属于某个 Library，所以封面风格由 Library 决定，书架只是「那张大图的一个缩略映射」。

实现：

后端的 bookshelf DTO 里增加一个派生字段：effective_cover_url 或 cover_url，在查询的时候直接 join Library：

SELECT
  b.id,
  ...,
  COALESCE(b.cover_url_override, l.cover_url) AS cover_url
FROM bookshelves b
JOIN libraries l ON b.library_id = l.id;


如果你暂时不做 override，就直接 l.cover_url。

前端不再自己 patch，不管是列表还是详情：统一用 API 返回的 bookshelf.cover_url 渲染。

当 Library 封面改了，你不需要更新一堆 bookshelf，只要下次请求时 join 一下就自动生效。

优点：

没有「同步问题」，领域上也合理：Library=空间风格，Bookshelf=房间里的柜子。

代码简单：所有缩略图走一个统一字段，不需要前端各种 if/else。

行业里很多系统这么做：由上游实体提供品牌/封面，下游实体只是露出“来自上游的主题色”。

建议你现在怎么落地？ / Practical suggestion

结合 Wordloom 现在的结构（Library → Bookshelf → Book → Block）：

短期（省事、稳）：

直接采用「方案 A：派生封面」：

Bookshelf 默认用 Library 的封面。

暂时不做“Bookshelf 自己换封面”的功能。

这样你只改后端 query + DTO + 前端统一读一个字段。