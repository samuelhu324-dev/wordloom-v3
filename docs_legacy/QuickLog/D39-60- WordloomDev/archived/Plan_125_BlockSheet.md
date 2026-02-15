现在里面那页“纸”已经挺像文档了，问题就是：外围一看有两层圆角+阴影，视觉上有点像「白纸套在白纸里」，专业感就被削弱了。

你现在大概是这种结构：

灰色背景
  └─ 外层大卡片（圆角 + 阴影 + 浅灰背景）
        └─ 内层“纸张”（白底 + 圆角）
              └─ Blocks…


所以会看到两个边框。

我给你一个“只保留一张纸”的做法，顺带写成可以直接丢给 Copilot 的规范。

1. 简化结构：外层只负责居中，视觉上只有一张纸

目标：

外层容器只管：左右居中、上下留白；

视觉上只出现一块白纸（圆角 + 阴影）；

建议改成：

// 外层：layout 容器，只做居中和留白
<div className="book-layout">
  {/* 这里可以有顶部导航 / tabs / 侧边栏 */}
  <main className="book-main">
    {/* 这就是唯一那张“纸” */}
    <article className="book-page">
      {/* Blocks 在这里 */}
    </article>
  </main>
</div>


CSS 规范：

/* 整个编辑页的背景 */
.book-layout {
  min-height: 100vh;
  background: #F3F4F6;           /* 淡灰蓝，和现在差不多 */
}

/* 主区域：居中 */
.book-main {
  max-width: 960px;              /* 视喜好可调：840 / 960 */
  margin: 24px auto 40px;        /* 上下留白 */
  padding: 0 16px;               /* 适配小屏 */
}

/* 唯一的“纸张” */
.book-page {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 32px 40px;            /* 里面的页边距 */
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.06);
  border: 1px solid rgba(15, 23, 42, 0.03);  /* 很轻的描边，可有可无 */
}


关键点：

把原来那层“外框”的 background / border 去掉，或者直接删掉那个 DOM；

页面上只有 .book-page 这一张白纸有圆角+阴影，其余只是平铺背景。

2. 如果你想保留“浅光晕”的感觉，避免双边框的方法

你现在截图里的外框有一点 内阴影/光晕 的感觉，也不是不能用，只是不要让内外两层都截断视觉。

可以这样调：

/* 外层：只做光晕，不要第二层边框 */
.book-main {
  max-width: 960px;
  margin: 24px auto 40px;
  padding: 0 16px;
}

/* 光晕可以通过 ::before 装饰，而不是再包一层卡片 */
.book-main::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(
    circle at top,
    rgba(255, 255, 255, 0.9),
    transparent 60%
  );
}


然后保持 .book-page 自己的白纸样式，就不会出现“白框嵌白框”。

3. 几条可以写进 VISUAL_RULES 的硬规则（给未来自己看）

你可以加这么一段：

- Block editor 使用「单页文档」视觉：
  - 页面背景为浅灰色 (#F3F4F6)，中间居中一张白色页面。
  - 页面只保留一层可见边框（book-page），外层容器不再绘制第二层白色卡片。
  - book-page 采用圆角 16px、轻微阴影和 32–40px 的内边距，营造纸张感。
  - 禁止出现白底圆角卡片内再嵌套一层白底圆角卡片（避免双边框）。


这样改完后，视觉效果会变成：

背景：淡淡一层灰蓝；

正中：只有一张白纸承载所有内容；

你的 Blocks、标题、引用这些都在同一张纸上，整体就会比现在专业很多、也更接近 Notion / Linear 文档那一派的审美。

等你那边 CSS 一调，整页氛围会一下子从“套娃卡片”变成“认真的编辑器页面”。