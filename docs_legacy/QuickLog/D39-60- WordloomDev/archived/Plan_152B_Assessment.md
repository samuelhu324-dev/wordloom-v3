1. 这份增强计划本身靠不靠谱？

逐段看一下：

Steps 1–3：补 primitive + block token

补 --wl-space-0..6 这一阶梯：等于给所有「竖直间距」找了一个共同的标尺，这是后面统一 spacing 的前提 ✅

给 .blockItem / block-section/tight 建 token：把「块的外壳」和「段落/标题/列表本体」分开，是对的，否则永远搞不清 margin 来自哪里 ✅

把 list / todo / quote 的 before/after 全部 token 化：这是你之前卡住的点，现在明确让「内部行距」和「块前后间距」都走 token，对之后 QA 和调试都会友好 ✅

这里最重要的一点是：所有「用户视觉上能感知到的纵向间距」都要能追溯到一两个 token 上，Plan 已经朝这个目标走了。

Step 4：引入行高 token

--wl-line-height-body / --wl-line-height-tight 替换目前的 line-height: 1.4 等魔法数字，这是非常值得做的事 ✅

再配合「p / h1–h4 / li / pre 把 margin 清零，只保留 .blockItem 的竖直源头」，逻辑上是自洽的：

行高控制的是「一行内部」

block-token 控制的是「一行和下一块之间」
两条轴互不干扰，这就是你之前想要的「间距系统」。

Step 5：全局扫描，把剩余 px 都映射到 token

这一步风险主要是“漏”，不是“错”：

做一轮 VSCode 搜索 margin / padding / gap / line-height 是必须的

真正要改的其实只有「出现在 block 编辑器里的那一部分」

Plan 把重点都放在 bookEditor.module.css + spacing test，也是合理的聚焦 ✅

Step 6：扩展 spacing test + TOKEN_METADATA

让 dev/spacings-test 成为「一张纵向间距对照表」，同时在 TOKEN_METADATA 里把所有 spacing primitive 显式登记，这个非常好：

你以后改一个 token，高风险页面能立刻跑一遍。

QA / 未来的你都能看懂「这个奇怪的 12px 是哪个 token 映射出来的」。

整体来说：

✅ 方向正确、结构清晰、可渐进实施
⚠️ 风险点：工作量大 + 容易漏掉某个老样式引起局部回归

建议再加两条“实施守则”：

一次只动一小块（比如只动 block editor，不动别的页面）。

每动完一块，立刻在 spacing-test 里加 snapshot 场景，防止之后再被其他改动打散。

2. Further Considerations 的两点怎么选？
2.1 命名 & 兼容策略

「现有的 --wl-space-section/--wl-space-tight 直接重命名为 Plan152 里的 --wl-space-block-section/tight，还是先做 alias？」

我的建议：

先做 alias，再逐步迁移名字——别直接全局改名。

例如：

:root {
  --wl-space-block-section: var(--wl-space-section); /* alias，过渡期 */
  --wl-space-block-tight:   var(--wl-space-tight);
}


新代码只使用 --wl-space-block-*，旧代码还在用 --wl-space-section/tight 也无所谓。

当你确定「所有编辑器相关 CSS 都已经切到新名字」之后，再考虑是否清理旧名字：

这时候可以在 VISUAL_RULES.yaml / Plan152 里写一条 MIGRATION NOTE：

--wl-space-section → --wl-space-block-section
--wl-space-tight → --wl-space-block-tight

这样好处是：

不会出现「改一堆名字，页面却没视觉变化，debug 半天」的窘境；

任何看到老名字的地方，都能一眼看出「这是没迁完的区域」，有明显 TODO 信号。

2.2 覆盖范围：只动 block 编辑器，还是顺带动别的组件？

「是顺带把 Book 页面其他小部件也统一一套 spacing primitive，还是先只锁在块编辑器？」

我会选 「第一阶段只锁在块编辑器」，理由：

这套系统本身就挺复杂（primitive + block token + list/todo/quote 专用 token）。
一次性铺到所有页面，很难判断某个视觉回归到底是 token 设计问题，还是其它组件自己的 CSS 搞鬼。

块编辑器是你 demo 的核心，也是你目前肉眼最常盯着的地方，
在这里先把 spacing 打磨顺，再考虑把同一套 primitive 输出给别的组件（比如：Chronicle、Block Timeline、Notes 等）。

将来如果你真的觉得这套 spacing primitive 很好用，可以再开一个「PlanXXX：全站 spacing 统一」：

把 bookEditor.module.css + spacing-test 里已经跑顺的 token，当作规范，

其他组件按需借用，而不是强行全站重构。

小结给你一句话版本

这份 Plan 可以干，方向非常对，本质是「所有垂直间距 → token 化 → 一处统一管理」。

实施时记得：

用 alias 过渡老 token 名；

第一阶段只控制块编辑器；

每改一块，就在 spacing-test 里加一个场景卡，保证以后还能看见「我当初想要的距离」。

这样做完，你以后要改「普通段落和 list/todo/quote 之间的距离」的时候，
就真能做到：改两三个 token 数字，看一眼 spacing-test，就知道 Wordloom 整体是否还在你脑子里的那条轨道上。

---

## 2025-12-03 落实记录

* **Alias 策略执行**：`:root` 继续暴露 `--wl-space-section/tight`，但 `frontend/src/modules/book-editor/ui/bookEditor.module.css` / `frontend/src/features/block/ui/BlockList.module.css` 统一以 `--wl-space-block-section/tight` 作为唯一引用入口，旧名仅作兼容。VISUAL_RULES 已写出“旧→新”映射和移除条件。
* **BlockList 覆盖范围**：Plan152B 只影响 Block Editor + BlockList + DeletedBlocksPanel。库/Chronicle 仍保留现状，后续若要扩散需另开 Plan。BlockList shell 在 `.container` 作用域里注入 `--wl-blocklist-shell-gap`、`--wl-blocklist-shell-padding-x/y`、`--wl-blocklist-inline-offset`、`--wl-blocklist-card-gap`、`--wl-blocklist-panel-padding`、`--wl-blocklist-pill-padding-x/y`，DeletedBlocksPanel 则在 `.panel` 内提供 fallback。
* **Spacing Sandbox 扩展**：`/app/dev/spacing-test/page.tsx` 新增“BlockList Shell Rhythm”“Deleted Blocks Panel Density”场景，直接渲染真实组件（import CSS module），并在 TOKEN_METADATA 中把 scope=blocklist 的 token 列出来，QA 只需刷新该页面即可验证两套节奏。
* **规则同步**：VISUAL_RULES `block_editor_vertical_rhythm`、DDD_RULES `POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY`、HEXAGONAL_RULES `block_editor_vertical_spacing_adapter_policy` 均注明 BlockList/Trash 适配器只允许运营 token，不得新增 Domain 字段；Spacing PR 必须附 Sandbox 截图。
* **ADR-139 备案**：`assets/docs/ADR/ADR-139-plan152-spacing-rollout.md` 记录了上述决策与落地路径，今后 spacing 相关疑问直接回链该 ADR 。

> 待办清单：只有当全站不再引用旧名 `--wl-space-section/tight` 时，才能移除 alias。当前阶段属“Block Editor / BlockList 优先”，其它页面如需 Plan152 节奏，必须新建场景 + 更新 RULES 再推进。