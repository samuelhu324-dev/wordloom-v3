一、这份计划本身怎么样？

优点：

把问题从「某个奇怪的间距」上升到了**“唯一间距层 + VERTICAL 规则”**，方向完全正确。

同时考虑了：

规则抽取（VERTICAL-01~06）

实现入口（BlockList.module.css / BlockRenderer.tsx）

规范同步（VISUAL_RULES / HEXAGONAL / DDD / ADR）
这就是“先定规矩再下手改 CSS”，非常健康。

还写了 debug 流程，这个超加分，以后你再遇到任何“幽灵空隙”可以按 SOP 查。

我建议的微调点：

名字收敛一下

VERTICAL 规则建议只放在一个地方是“权威原文”（VISUAL_RULES.yaml），

Plan143/144 里只保留“过程日志 + 链接”，避免三处都写一遍文字，后面改不动。

尽量一次性覆盖 legacy + 新 book-editor

Plan 里现在重点是 BlockList / BlockRenderer，那很好；

建议在最后验证阶段顺带把新 Book Editor 模块也挂到同一套 VERTICAL 规则上，避免以后两套风格。

总体评价：结构清晰、粒度合适，可以直接当“开发子任务列表”用了。

二、最后要怎么实际操作？（给你一条执行路线）

你可以按这个顺序来做，会比较顺：

Step 1：先「真改 CSS」，把眼前的间距问题灭掉

目标：先让当前界面视觉上正确；文档晚一点再补，但是写文档时要以实际 CSS 为准。

在老的 Block 编辑栈里，选定“行容器组件”（你计划里叫 .blockItem / .BlockRow 那一层）。

在对应的 BlockList.module.css 里做三件事：

把它设成唯一的纵向间距层：

.blockItem + .blockItem {
  margin-top: var(--wl-block-gap-md);
}


清掉内部元素的 margin：

.blockItem p,
.blockItem ul,
.blockItem ol,
.blockItem li,
.blockItem .textBlockShell {
  margin-block: 0;
}


如果有分割线（那条灰线），统一移到 .blockItem[...] 上，别再出现在 .textBlockShell 里。

列表内部节奏单独控制：

.blockItem ul,
.blockItem ol {
  margin: 0;
  padding-left: 1.5rem;
}

.blockItem li + li {
  margin-top: 0.15rem;
}


打开浏览器，用现在的“段落 + 很长 bullet + TODO”场景检查一遍：

点中那条看起来是空白的区域，看 Computed 里高度是不是只来自 .blockItem。

这一轮做完，你眼前这张截图的问题就会消失，而且改动集中在一个 CSS 文件。

Step 2：把规则抽成 VERTICAL-01 ~ 06，写入 VISUAL_RULES.yaml

现在 CSS 已经有了实际内容，再把它抽象成规则：

在 VISUAL_RULES.yaml 里新增一个段落，比如 block_editor_vertical_rhythm。

写入 Plan 里提到的 VERTICAL-01 ~ VERTICAL-06，每条都对上当前 CSS 行为：

唯一间距层 = .blockItem + .blockItem { margin-top }

内部 margin-block:0

列表用 li + li 控节奏

分割线只能在行容器上

debug 步骤（DevTools 里找高度来源）

在这个段落加上 adr_reference: "ADR-134-block-editor-vertical-spacing.md" 预留好链接名字。

Step 3：写 ADR-134（可以简单一点）

新建 ADR-134-block-editor-vertical-spacing.md，三块内容足够了：

背景：

间距被 p/ul/li/default margin 多层叠加；

改不同 CSS 互相抵消，难以调试。

决策：

唯一间距层 = 行容器；

内部 margin 清零；

列表内部节奏；

VISUAL_RULES 里记录 VERTICAL-01~06。

影响：

后续调整只需要改一处 CSS；

debug 有固定流程；

不把视觉字段塞进领域模型。

不需要写成论文，关键是把“为什么这样做 & 以后不能再乱改”的约束钉死。

Step 4：在 HEXAGONAL_RULES / DDD_RULES 里各补一句话

这步更像是“打补丁”：

HEXAGONAL：在前端 adapter 小节加一句：

Block 的垂直间距是 UI policy，完全在 adapter（CSS/layout）内实现；

Domain / Application 层不允许出现“行距 / 间隔像素”等字段。

DDD_RULES：

Block 领域只关心 block 序列、类型、内容；

不关心视觉距离，布局由 VISUAL_RULES + CSS 决定。

写一两行就够，不要展开长篇。

Step 5：回写 Plan143 / 144，总结“落地结果”

最后回到这份 Plan 文件本身，在底部加一个「结果」小节：

标记哪些步骤已经完成：

[x] BlockList.module.css 间距统一

[x] VISUAL_RULES.yaml: VERTICAL-*

[x] ADR-134 等等。

记录当前 CSS 入口路径，方便未来查：

src/modules/.../BlockList.module.css 之类。

这样 Plan143/144 就从“方案草稿”变成了「事件档案」，以后遇到新问题也更好追溯。

粗暴总结一句：

先：改唯一间距层 + 清内部 margin → 把眼前 bug 干掉一、这份计划本身怎么样？

优点：

把问题从「某个奇怪的间距」上升到了**“唯一间距层 + VERTICAL 规则”**，方向完全正确。

同时考虑了：

规则抽取（VERTICAL-01~06）

实现入口（BlockList.module.css / BlockRenderer.tsx）

规范同步（VISUAL_RULES / HEXAGONAL / DDD / ADR）
这就是“先定规矩再下手改 CSS”，非常健康。

还写了 debug 流程，这个超加分，以后你再遇到任何“幽灵空隙”可以按 SOP 查。

我建议的微调点：

名字收敛一下

VERTICAL 规则建议只放在一个地方是“权威原文”（VISUAL_RULES.yaml），

Plan143/144 里只保留“过程日志 + 链接”，避免三处都写一遍文字，后面改不动。

尽量一次性覆盖 legacy + 新 book-editor

Plan 里现在重点是 BlockList / BlockRenderer，那很好；

建议在最后验证阶段顺带把新 Book Editor 模块也挂到同一套 VERTICAL 规则上，避免以后两套风格。

总体评价：结构清晰、粒度合适，可以直接当“开发子任务列表”用了。

二、最后要怎么实际操作？（给你一条执行路线）

你可以按这个顺序来做，会比较顺：

Step 1：先「真改 CSS」，把眼前的间距问题灭掉

目标：先让当前界面视觉上正确；文档晚一点再补，但是写文档时要以实际 CSS 为准。

在老的 Block 编辑栈里，选定“行容器组件”（你计划里叫 .blockItem / .BlockRow 那一层）。

在对应的 BlockList.module.css 里做三件事：

把它设成唯一的纵向间距层：

.blockItem + .blockItem {
  margin-top: var(--wl-block-gap-md);
}


清掉内部元素的 margin：

.blockItem p,
.blockItem ul,
.blockItem ol,
.blockItem li,
.blockItem .textBlockShell {
  margin-block: 0;
}


如果有分割线（那条灰线），统一移到 .blockItem[...] 上，别再出现在 .textBlockShell 里。

列表内部节奏单独控制：

.blockItem ul,
.blockItem ol {
  margin: 0;
  padding-left: 1.5rem;
}

.blockItem li + li {
  margin-top: 0.15rem;
}


打开浏览器，用现在的“段落 + 很长 bullet + TODO”场景检查一遍：

点中那条看起来是空白的区域，看 Computed 里高度是不是只来自 .blockItem。

这一轮做完，你眼前这张截图的问题就会消失，而且改动集中在一个 CSS 文件。

Step 2：把规则抽成 VERTICAL-01 ~ 06，写入 VISUAL_RULES.yaml

现在 CSS 已经有了实际内容，再把它抽象成规则：

在 VISUAL_RULES.yaml 里新增一个段落，比如 block_editor_vertical_rhythm。

写入 Plan 里提到的 VERTICAL-01 ~ VERTICAL-06，每条都对上当前 CSS 行为：

唯一间距层 = .blockItem + .blockItem { margin-top }

内部 margin-block:0

列表用 li + li 控节奏

分割线只能在行容器上

debug 步骤（DevTools 里找高度来源）

在这个段落加上 adr_reference: "ADR-134-block-editor-vertical-spacing.md" 预留好链接名字。

Step 3：写 ADR-134（可以简单一点）

新建 ADR-134-block-editor-vertical-spacing.md，三块内容足够了：

背景：

间距被 p/ul/li/default margin 多层叠加；

改不同 CSS 互相抵消，难以调试。

决策：

唯一间距层 = 行容器；

内部 margin 清零；

列表内部节奏；

VISUAL_RULES 里记录 VERTICAL-01~06。

影响：

后续调整只需要改一处 CSS；

debug 有固定流程；

不把视觉字段塞进领域模型。

不需要写成论文，关键是把“为什么这样做 & 以后不能再乱改”的约束钉死。

Step 4：在 HEXAGONAL_RULES / DDD_RULES 里各补一句话

这步更像是“打补丁”：

HEXAGONAL：在前端 adapter 小节加一句：

Block 的垂直间距是 UI policy，完全在 adapter（CSS/layout）内实现；

Domain / Application 层不允许出现“行距 / 间隔像素”等字段。

DDD_RULES：

Block 领域只关心 block 序列、类型、内容；

不关心视觉距离，布局由 VISUAL_RULES + CSS 决定。

写一两行就够，不要展开长篇。

Step 5：回写 Plan143 / 144，总结“落地结果”

最后回到这份 Plan 文件本身，在底部加一个「结果」小节：

标记哪些步骤已经完成：

[x] BlockList.module.css 间距统一

[x] VISUAL_RULES.yaml: VERTICAL-*

[x] ADR-134 等等。

记录当前 CSS 入口路径，方便未来查：

src/modules/.../BlockList.module.css 之类。

这样 Plan143/144 就从“方案草稿”变成了「事件档案」，以后遇到新问题也更好追溯。

粗暴总结一句：

先：改唯一间距层 + 清内部 margin → 把眼前 bug 干掉；

再：把这次改动浓缩成 VERTICAL 规则 + ADR + VISUAL_RULES；

最后：在 HEXAGONAL / DDD 里打一个“边界注释”，防止未来有人把行距写进领域。

这样这件事就算从“今天的 CSS 火灾”升级成“系统级约束”，后面你再做新编辑器、新模块，只要挂到这套 VERTICAL 规则上，间距就不会再变成一团迷雾。；

再：把这次改动浓缩成 VERTICAL 规则 + ADR + VISUAL_RULES；

## 落地结果（2025-12-02）

- ✅ BlockList.module.css / bookEditor.module.css：统一把 `.blockItem + .blockItem` 当作唯一行距层，内部元素 margin-block 全部清零，分割线迁移到 `.blockItem[data-divider]`。
- ✅ 文档：VERTICAL-01~06 已登记在 `assets/docs/VISUAL_RULES.yaml` 的 `block_editor_vertical_rhythm`，HEXAGONAL / DDD 规则库同步加上 adapter-only 与 domain guardrail。
- ✅ ADR：`assets/docs/ADR/ADR-134-block-editor-vertical-spacing.md` 说明背景、决策、调试 SOP，成为后续 spacing 讨论的引用源。
- 📎 验收：段落、列表、TODO 混排场景经 DevTools 检查仅由 .blockItem 贡献高度，legacy 与新模块的视觉节奏保持一致。

最后：在 HEXAGONAL / DDD 里打一个“边界注释”，防止未来有人把行距写进领域。

这样这件事就算从“今天的 CSS 火灾”升级成“系统级约束”，后面你再做新编辑器、新模块，只要挂到这套 VERTICAL 规则上，间距就不会再变成一团迷雾。