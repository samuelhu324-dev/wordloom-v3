你这个「点一下整行弹起来」的违和感，我完全能想象到——现在的交互很像：
原来在看网页，点一下突然变成「白底表单 + 三行 textarea」，整段文字被迫换衣服。

我帮你拆成三块来改，而且都写成可以直接丢给 Copilot 的规范。

1. 问题拆解一下

从截图看，现在大概是这样：

view 状态：

只显示一行文字（AAAAA）

没有灰底，没有图标

edit 状态（微编辑器）：

外面套了一层灰底卡片（带 padding + border + shadow）

里面用 textarea 或 contenteditable div，行高 / 字号和外面不一样

默认 min-height 很高，看起来像三行的高度

右上角出现图标（时钟 + 删除）

导致三个问题：

点击时高度变高、字位置变了 → “弹一下”

字号/行距看起来不一致 → 像换了字体

默认为三行高 → 很占空间，打断流文档感

2. 规则一：view / edit 必须用同一套排版，不准换衣服

给 Copilot 说白一点：

「标题的 view 和 edit 状态用同一个 class，
edit 时只改背景和边框，不改 font-size / line-height / font-weight。」

可以规定成：

/* 所有 H1 block 的基本排版，不区分查看/编辑 */
.block-heading-1-text {
  font-size: 20px;
  line-height: 1.5;
  font-weight: 600;
}

/* 外层“微编辑 shell”统一高度，不要改字体 */
.block-heading-shell {
  border-radius: 8px;
  padding: 6px 10px;
  border: 1px solid transparent; /* 关键：默认也占位 */
  transition: background-color 0.12s ease, border-color 0.12s ease, box-shadow 0.12s ease;
}

/* 编辑/聚焦态：只改背景和边框颜色，不改 padding / 字号 */
.block-heading-shell--editing {
  background-color: #F9FAFB;
  border-color: #E5E7EB;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}


组件结构建议：

function HeadingBlock({ isEditing, ... }) {
  const shellClass = clsx(
    "block-heading-shell",
    isEditing && "block-heading-shell--editing",
  );

  return (
    <div className={shellClass}>
      <div className="block-heading-1-text">
        {/* 这里不换标签，只是加 contentEditable 或挂编辑器 */}
      </div>
      {isEditing && <BlockActions />}
    </div>
  );
}


重点：

view / edit 都用 .block-heading-1-text，编辑状态不要再切到别的 class。

外壳 .block-heading-shell 的 padding、border-width 在两种状态一致，
只用透明边框 → 有占位但看不见，这样切换时就不会“抬头、加粗、抖一下”。

3. 规则二：微编辑器默认只占一行，高度按内容自适应

你现在的问题是：textarea 的 min-height 太大，看起来像预留了三行。

给 Copilot的具体要求可以这样写：

「标题的编辑器默认只占一行高度（min-height 约等于一行文字），
随着输入内容自动增高，但最多显示 3 行（超出用滚动）。」

代码草稿：

function AutoSizeTextarea(props: { value: string; onChange: ... }) {
  const ref = useRef<HTMLTextAreaElement | null>(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "0px";                         // reset
    const next = Math.min(el.scrollHeight, 3 * 24);  // 24 = 行高 * 字号，可按实际调
    el.style.height = `${next}px`;
  }, [props.value]);

  return (
    <textarea
      ref={ref}
      rows={1}
      className="heading-input"
      {...props}
    />
  );
}


配合 CSS：

.heading-input {
  width: 100%;
  resize: none;
  overflow: hidden;       /* 超出的由 JS 控 height 控制 */
  border: none;
  background: transparent;
  font: inherit;          /* 关键：继承父节点字体、行高 */
  padding: 0;
  margin: 0;
}


关键点翻译一下：

font: inherit → 保证编辑时字体和 view 态完全一致；

rows={1} + JS 调整 height → 默认就是单行高度；

你可以把 3 * 24 换成 3 * 行高(px)，实现最多三行高的天花板。

如果你不用 textarea，而是 contenteditable div，也可以用相同思路：
不要给它写死 3 行高的 min-height。

4. 规则三：图标和背景要「贴边」而不是「占行高」

现在图标在右上角，而且一出现就让整个区域看起来像大卡片。
可以这样给 Copilot下指令：

icon 只在 hover + editing 时显示，其余时间隐藏；

icon 用绝对定位，不参与行高计算。

示例：

.block-heading-shell {
  position: relative;
}

.block-heading-actions {
  position: absolute;
  top: 4px;
  right: 6px;
  display: flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
}

.block-heading-shell--editing .block-heading-actions,
.block-heading-shell:hover .block-heading-actions {
  opacity: 1;
  pointer-events: auto;
}


这样：

文字的布局不会因为图标出现/消失而左右晃；

再配合前面说的透明边框 + 固定 padding，
整个 Block 在 view/edit 之间就只有轻微颜色变化，不会「放大缩小」。

5. 规则四：让整页更像流动文档的几条硬约束

给 Copilot一句话版规范，你可以原封不动写进 VISUAL_RULES 里：

- Heading / paragraph blocks must not change font-size or line-height between read and edit states.
- Block shells use transparent borders in idle state so that entering edit does not change layout.
- Heading micro editor default height is 1 line; auto-grow with content but cap at 3 lines.
- Per-block background and icons are only visible on hover or editing, not in idle read mode.
- Icons must be absolutely positioned and not affect line height.


中文再补充一条给自己看：

标题在未编辑状态下，看起来就像普通文档标题；
点击进入编辑时，只是「背景稍微亮一点 + 右上角出现两个小图标」，
禁止再把它变成一块厚厚的大卡片。

简单收个尾：

你现在这个“弹一下”的根本原因就是：view/edit 两个完全不同的盒模型。

把字体 + padding + border-width 固定一致，只改颜色和阴影，就能把抖动消掉。

再把 textarea 改成「单行起步 + 自动高度」，你那种「一点击就冒出三行空白」的违和感也会不见。

你把上面那几段 CSS+规范丢给 Copilot，它就会知道：
“不要再帮我搞花里胡哨的卡片编辑器，我要的是 Google Docs 那种：点击后几乎不变，只是能打字的标题”。