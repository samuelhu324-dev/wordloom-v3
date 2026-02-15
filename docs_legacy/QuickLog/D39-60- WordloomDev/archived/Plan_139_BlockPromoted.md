Block 间距现在哪里怪？怎么微调？

看你第二张图，大概有几个点：

段落 → TODO 之间的空白有点大

TODO 与 TODO 之间的间距和普通段落一样大，看起来不像「一组」

底部那块大虚线「写点什么…」区域高度略高，视觉上有点抢戏

一个比较干净的做法：

定一套「垂直节奏」变量

例如（以 4px 为单位）：

:root {
  --block-gap-xs: 4px;   /* 列表项内部、todo 列内部 */
  --block-gap-sm: 8px;   /* 普通段落之间 */
  --block-gap-lg: 16px;  /* 不同类型/段落组之间 */
}

规则建议：

同类型 block 连在一起 → 用小间距

.blockItem.paragraph + .blockItem.paragraph {
  margin-top: var(--block-gap-sm);
}

.blockItem.todo + .blockItem.todo {
  margin-top: var(--block-gap-xs);
}


不同类型之间 → 拉开一点，表示「段落组」分界

.blockItem.paragraph + .blockItem.todo,
.blockItem.todo + .blockItem.paragraph {
  margin-top: var(--block-gap-lg);
}


底部整体“写点什么…”容器
保留一定高度，但不需要那么高，比如：

.blockList-footerPlaceholder {
  min-height: 3rem;         /* 够点一下就出新块就行 */
  padding: 0.75rem 1rem;
}


这样看上去会变成：

一段正文：行距舒服

下面紧接一组 todo：整体和正文之间有一条明显的「过渡空白」

组内 todo 项之间很紧凑，像一串有机整体

整体观感会专业很多。

////////////////////////////////////////////////////////////////

这个问题很好，因为现在这块真的挺干净的，再多丢一个按钮很容易把气质毁掉 😂
我们先看一下你现在这行 TODO 的构成：

左边：☑

中间：写点什么…（inline editor）

右边：一颗很淡的 …（block 级菜单）

你要做的事情只有一件：

给这颗 TODO 增加一个 promoted: boolean 状态，
但控制这个状态的入口要尽量藏起来，只在“我真的想操作”的时候出现。

1. 入口：塞进现有的 … 菜单里（默认不露头）

这是最不打扰人的方案，也是我最推荐的：

不在行内再加任何新的 icon

只在你点开右侧 … 的时候，出现一个菜单项：

提升到 TODO 仪表盘 / 从 TODO 仪表盘移除

默认状态下，这个功能完全隐形，界面仍然像现在这么干净

行为大概是：

promoted === false 时：菜单里显示
🔼 提升到 TODO 仪表盘

promoted === true 时：菜单里显示
⬇ 取消提升

这样做的好处：

操作频率本来就不高，放在二级菜单一点问题没有

不会增加任何“常驻 UI 噪音”

2. 状态反馈：只给「已提升」的 TODO 一个非常轻量的标记

入口藏得这么深，有个问题：我怎么知道这个 TODO 已经被提升过了？

解决方式也要“极低噪音”：

不要做一个大的按钮，而是一个小小的「状态点」或「徽标」

比如在右侧 … 左边加一个淡淡的标签，只在 promoted === true 时显示：

例子 1（文字徽标）：

☑ 写点什么…                             [提]  …


例子 2（小圆点）：

☑ 写点什么…                              ●  …


颜色建议：

不要用主按钮蓝，太抢眼

用一个偏灰蓝 / 灰紫的小圆点或小字，比正文略浅一点

鼠标 hover 到这个标记上可以出一个 tooltip：已提升到 TODO 仪表盘

交互上这个标记不需要可点击，点 … 进去改即可，这样它只是一个“状态灯”，不会让界面显得复杂。

3. 直接给 Copilot 的说明（英文，方便它帮你改代码）

你可以把下面这段丢到 TodoBlock / BlockItem 顶部注释或一个 PLAN_TODO_PROMOTION.md 里：

// Feature: "Promote" TODO blocks into the Maturity → TODO dashboard
//
// Requirements:
// 1. Each TODO block gets a new boolean field `promoted`.
//    - promoted = false (default): this TODO is only local to the block.
//    - promoted = true: this TODO is also shown in the Maturity/TODO tab.
//
// 2. UI entry should be very low-noise:
//    - We already have a per-block kebab menu ("...") on the right.
//    - Add a menu item inside that menu to toggle the flag:
//
//      - When promoted === false:
//          "🔼 Promote to TODO dashboard"
//      - When promoted === true:
//          "⬇ Remove from TODO dashboard"
//
//    - No extra always-visible buttons should be added to the row.
//
// 3. Visual feedback for promoted TODOs:
//    - Only when `promoted === true`, show a very subtle status badge near
//      the kebab menu on the right.
//
//    Example layout:
//
//      [ ] Write something…                        [PROMOTED]  ...
//
//    Implementation idea:
//      - Add a small <span> with class "todo-promotedBadge" before the kebab.
//      - For non-promoted items, do not render this span at all.
//
//      CSS sketch:
//
//        .todo-promotedBadge {
//          font-size: 11px;
//          color: var(--color-muted-blue); // lighter than main text
//          margin-right: 4px;
//        }
//
//        /* Alternatively, use a small dot instead of text */
//        .todo-promotedBadge::before {
//          content: "●";
//          font-size: 10px;
//        }
//
// 4. Maturity/TODO panel should only show TODOs where:
//      block.kind === 'todo' && block.done === false && block.promoted === true
//
// This keeps the block editor UI clean (no extra always-visible controls),
// while still allowing power users to "promote" important TODOs into the
// dashboard via the kebab menu.

小结一嘴

入口：塞进右侧 … 菜单，完全不占常驻空间

状态：只给已提升的 TODO 一个很轻的小标记（徽标或圆点）

查询：仪表盘只看 done === false && promoted === true

这样你既保住了现在这块「干净到发光」的编辑界面，又把“提升”这个专业能力藏在一个只有你自己知道的暗门里，非常符合 Wordloom 这种「低调但有深度」的气质。