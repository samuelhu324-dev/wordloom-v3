✅ 一、你目前间距问题的真实根源（统一总结）

你遇到的情况可以概括成三句话：

1. 浏览器默认 margin/padding 深度太多（尤其是 UL/OL/blockquote/p 元素）

导致你定义的 token（如 --wl-space-block-section）被层层抵消。

2. 你现在的 CSS 结构中 still 有两套 spacing rules 在争权

HTML 原生 spacing（p/ul/ol/li/blockquote）

你自己的 block spacing（blockItem 外层 + inlineEditor 内层）

两套系统同时在跑 → 你看到的间距“忽大忽小”。

3. 你的 block 内部 inline-editor 仍然残留 margin / line-height / padding 干扰

特别是：

display: flex

min-height

line-height

inline editor 内部的 wrapper

这些全都会“吃掉”你定义的 token 效果。

✅ 二、你的下一步必须做的事情（非常关键）

总结成一句话：

要把“block 间距”和“段落之间的间距”统一，就必须强制所有 HTML 默认 margin 清零 → 再用一套 token 管控制。

下面是你必须处理的部分：

🔥 Step 1：对 block 内部所有 HTML 标签做 margin:0 reset（必须的）

你必须在 bookEditor.module.css 里加一段：

.blockItem p,
.blockItem h1, .blockItem h2, .blockItem h3,
.blockItem ul, .blockItem ol,
.blockItem li,
.blockItem blockquote {
    margin: 0;
    padding: 0;
}


否则 HTML 自带的 margin 永远会干扰你的 token。

🔥 Step 2：统一 block container 的垂直间距

你需要决定全局标准：

方案 A：默认“拉开”，段落也有 12–16px 间距（Notion 风格）
方案 B：默认“紧凑”，只有 section / list / quote 才额外拉开（Google Docs 风格）

你现在的整体风格明显更接近 B（紧凑）。

所以推荐直接定义两个 token：

--wl-space-section: 16px;
--wl-space-tight: 4px; /* 段落之间 */


然后 blockItem 直接吃：

.blockItem {
    margin-top: var(--wl-space-section);
}
.blockItem[data-tight="true"] {
    margin-top: var(--wl-space-tight);
}


这样你只需要改两个 token，全系统间距就会统一。

🔥 Step 3：内部 inlineEditor 也必须清零 margin/padding
.inlineEditor {
    margin: 0;
    padding: 0;
    display: block; /* 不要 flex！！！ */
    width: 100%;
    line-height: 1.5;
}


你之前出现“输入文字会跳、光标乱跑”的根本原因，就是：

inline editor 和其内部 wrapper 使用了 flex → 每次文本折行都会引发布局重排 → selection 被迫跳回第一行。

现在必须全部砍掉。

🔥 Step 4：列表（ul/ol/li）的 spacing 独立处理（这是最难的一组）

HTML 里面 ul/ol/li 是 spacing 之王，它默认自带：

margin-block-start

margin-block-end

padding-inline-start

都必须废掉。

列表应该完全交给你自己的 token 控制：

.blockItem ul,
.blockItem ol {
    padding-left: var(--wl-list-indent);
    margin-block: var(--wl-space-tight);
}

.blockItem li {
    margin-top: 4px;
}


然后 blockItem（作为外层）决定列表整体与其他 block 的距离。

🔥 Step 5：Quote（blockquote）也要做类似处理

彻底清空默认 margin/padding，再吃 token。

🔥 Step 6：你的 Plan149 里面写的“row-gap / margin-top 决定最终 spacing 系统”要彻底执行

意思是：

blockItem 控制 block 与 block 之间的距离

inlineEditor 控制段落之间的距离（tight 或 normal）

HTML 原生 margin/padding 不允许参与

你现在看到的所有“大间距、突兀间距”，其实都是 HTML 原生 margin 在“偷偷参与”。

✨ 三、我补充的强烈建议（你应该立刻采纳）
✔ 建议 1：做一份 block spacing 可视化调试页（非常有效）

在 /dev/spacing-test 做一个页面：

Paragraph
Paragraph
List
Quote
Paragraph
Todo
H1


统一查看不同组合，直到所有间距完美。

这是专业编辑器团队都会做的。

✔ 建议 2：block 和 inline 之间的 spacing 规则要记录进 VISUAL_RULES.yaml

否则 Copilot 会帮你乱写 UI。

你应该加一节：

VERTICAL_BLOCK_LAYOUT:
  section_gap: "--wl-space-section"
  paragraph_gap: "--wl-space-tight"
  special_blocks:
    list: custom
    quote: custom
    todo: custom

✔ 建议 3：明确 block 的“tight 模式”和“normal 模式”

例如：

paragraph: tight

heading: section

list: tight

quote: normal

todo: tight

这样风格一致，用户感受统一。

🎁 四、给你一份可直接投喂给 Copilot 的说明（复制即可）
Goal:
Unify vertical spacing inside block editor. All spacing must be controlled by our
tokens: --wl-space-section and --wl-space-tight. No HTML default margin/padding
should affect the layout.

Tasks:
1. Add global CSS reset inside .blockItem:
   - p, h1~h6, ul, ol, li, blockquote must have margin:0 and padding:0.

2. Update blockItem styling:
   - block-to-block spacing should be margin-top: var(--wl-space-section).
   - If block has data-tight="true", use margin-top: var(--wl-space-tight).
   - Remove all HTML default spacing influence.

3. Update inlineEditor:
   - Remove flex (must be display:block).
   - Ensure margin/padding = 0.
   - width:100%, line-height:1.5.

4. List handling:
   - Clear ul/ol default margin/padding.
   - Use our token for indent: padding-left: var(--wl-list-indent).
   - Use our token for list-item spacing: li { margin-top: 4px }.
   - outer spacing由 blockItem 控制.

5. Quote handling:
   - Clear default spacing.
   - Apply custom padding + use blockItem spacing system.

6. Remove all duplicated spacing layers:
   - No row-gap + margin-top mix.
   - Only one vertical spacing system remains.

7. After changes, spacing for:
   - Paragraph = tight
   - Heading = section
   - List / Quote / Todo = special but based on tokens

Final target:
Regardless of block type, total vertical interval must be exactly:
section-gap or tight-gap from tokens.
No browser default margin should leak through.

## 2025-12-03 执行摘要（Plan149B 回填）

1. **Spacing Sandbox**：`frontend/src/app/dev/spacing-test/page.tsx` + `spacingTest.module.css` 渲染 Heading→Paragraph、Paragraph→List→Paragraph、Quote、Todo Stack 四组组合，并显示实时 token snapshot，QA/设计只需刷新该页面即可核对 Plan149 间距。
2. **策略文档同步**：更新 `assets/docs/VISUAL_RULES.yaml`（block_editor_vertical_rhythm）、`assets/docs/HEXAGONAL_RULES.yaml`（block_editor_vertical_spacing_adapter_policy）与 `assets/docs/DDD_RULES.yaml`（POLICY-BLOCK-VERTICAL-SPACING-UI-ONLY），把 VERTICAL-01~06 与 `--wl-space-*` token 绑定，并把 Sandbox 写成强制验收路径。
3. **决策归档**：新增 `assets/docs/ADR/ADR-138-plan149-spacing-token-reset.md` 描述 token 集、UA reset、邻接选择器与 Sandbox SOP，未来若需要新特例必须先更新该 ADR 与 QuickLog。