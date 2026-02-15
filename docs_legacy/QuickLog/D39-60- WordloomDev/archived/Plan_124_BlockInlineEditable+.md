这个感觉我懂，现在右上角一排 3 个小圆圈，虽然已经是 hover 才出现，但因为：

有品牌蓝 + 鲜红色删除

都是实心圆 + 边框

所以一蹦出来还是很“抢戏”，整段文档瞬间从「安静的文章」变成「UI 控件集市」。

可以从三层下手：**颜色减弱、数量减弱、出现方式减弱。**我给你一套可以直接丢给 Copilot 的规范。

1. 颜色 & 视觉权重减弱（低对比 + 无填充）

目标：让图标变成铅笔灰线稿，只在你盯着它的时候才看得清。

给 Copilot 的要求可以这样写：

.block-item-actions button {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  border: 1px solid transparent;  /* 默认透明边框 */
  background: transparent;        /* 不要白底小药丸 */
  color: #9CA3AF;                 /* 灰色图标，不要品牌蓝/红 */
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.5;                   /* 默认半透明 */
}

/* hover 到这一颗按钮上时才变清晰一点 */
.block-item-actions button:hover {
  opacity: 1;
  background: #F3F4F6;            /* 很浅的灰底，别用亮色 */
  border-color: #E5E7EB;
}

/* 删除按钮也别再用大红色底，只在 icon 上点红色 */
.block-item-actions button--danger {
  color: #DC2626;                 /* 红色只在 icon 线条上 */
}


搭配原本的：

.block-item-actions {
  position: absolute;
  top: 4px;
  right: 8px;
  display: flex;
  gap: 4px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease;
}

.block-item:hover .block-item-actions,
.block-item--editing .block-item-actions {
  opacity: 1;              /* 整组出现 */
  pointer-events: auto;
}


效果：

再也不会有三个彩色小球冲出来；

一眼看去还是文章，只有你把鼠标移到右上角，灰色小线条才稍微亮一点。

2. 数量减弱：非激活块只露一个 + 就够了

现在任何 hover 都是 + / 时钟 / 垃圾桶 三连。
可以改成：

当前正在编辑的 block（光标在里面） → 显示全部 3 个图标

只是鼠标划过的 block → 只显示一个淡淡的 + 或者一个「⋯」菜单

给 Copilot 的规则可以这样写：

const isActive = block.id === activeBlockId; // 光标所在的 block

// JSX 上：
<div className="block-item-actions">
  {isActive ? (
    <>
      <button onClick={insertBelow}>+</button>
      <button onClick={showHistory}>🕒</button>
      <button className="block-item-actions__danger" onClick={deleteBlock}>🗑</button>
    </>
  ) : (
    <button onClick={insertBelow}>+</button>  // 非激活块只露一个 +
  )}
</div>


这样：

你在正常阅读 / 滚动时，偶尔看到一两个淡灰色的小 +，存在感很低；

真正准备对某一段动刀子时（点进去编辑、光标在里面），才露出完整操作组。

3. 出现方式减弱：加一点延迟，防止鼠标划过去“闪一条”

还有一个小 trick：
当鼠标只是快速滑过页面时，不需要立刻展示 actions，可以加一个非常短的 delay，比如 150–200ms。

伪代码：

function useHoverActionsDelay() {
  const [visible, setVisible] = useState(false);
  const timer = useRef<number | null>(null);

  const onMouseEnter = () => {
    timer.current = window.setTimeout(() => setVisible(true), 150);
  };

  const onMouseLeave = () => {
    if (timer.current != null) {
      window.clearTimeout(timer.current);
      timer.current = null;
    }
    setVisible(false);
  };

  return { visible, onMouseEnter, onMouseLeave };
}


使用：

const { visible, onMouseEnter, onMouseLeave } = useHoverActionsDelay();

<div className="block-item" onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
  ...
  {visible && <BlockItemActions ... />}
</div>


这样：

你慢慢停在某一行 → 图标淡淡出现；

你只是滑鼠滚轮往下滚 → 因为停留时间 < 150ms，图标根本不会出现，页面更干净。

4. 总结成几条 VISUAL_RULES 里的“死规矩”

可以写成这样：

- Block actions (add / history / delete) must be visually de-emphasized:
  - Use low-contrast gray icons with transparent background by default.
  - Do not use solid brand colors or solid red pills as default states.
- For non-active blocks, only show a single "+" action on hover; show full action set only for the active (focused) block.
- Actions appear after a short hover delay (~150ms) to avoid flickering while scrolling.
- Action icons are absolutely positioned outside the main text column and must not change line height or layout.


照着这个调完之后，整体感觉会变成：

页面 99% 时间还是一篇安静的文档；

你轻轻把鼠标停在某一段右上角，才慢慢浮现出一小串灰色工具按钮；

真正要“动手术”的那一段会多两个红点（删除等），其他段落几乎看不到控件。

就是从「到处是 UI 控件」→「文档是主角，控件是侧边小工具」的转变。