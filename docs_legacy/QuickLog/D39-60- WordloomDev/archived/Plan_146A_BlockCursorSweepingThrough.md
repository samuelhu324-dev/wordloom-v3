这个“从第一个字扫到点击位置”的感觉，本质上是：

浏览器已经帮你把光标放好了，你的代码又在“多此一举”地重新设置了一遍选区，而且还是用了一条从 0 → offset 的 range。

于是眼睛看到的是：
先在行首闪一下 / 拉出一条选区 → 又瞬间收缩到你点击的位置，就像“扫过去”。

我分两层说：为什么会这样，以及一套比较干净的解决方式。

一、为什么会出现“扫过去”的视觉效果？

最常见的几种情况（你之前做 selectionStore / 恢复光标、命令式控制的时候，很容易踩到这些）：

点击时触发了重渲染 + 手动恢复旧选区

用户点击某个 block：

浏览器：已经把 caret 放在你点的位置了 ✅

React：你在 onClick/onFocus 里 setState 导致 block 重渲染

useEffect([blocks])：看到“block 列表变了”，就根据 selectionStore 去恢复上一次记录的光标位置（比如之前在行首）

所以你会先看到光标回到旧位置，然后再被别的逻辑推回去 / 再次点击时跳来跳去。

恢复选区的代码走了“两段式”range

典型写法是（伪代码）：

const range = document.createRange();
range.setStart(node.firstChild, 0);
range.setEnd(node.firstChild, offset); // 产生一个 0..offset 的“选中区域”
range.collapse(false); // 再 collapse 到末尾
selection.removeAllRanges();
selection.addRange(range);


视觉上就是：
“从第一个字到你要的位置被选中了一次，然后才缩成一个闪烁的光标”，所以你会感觉它“扫过去”。

正确做法应该是一次性设到目标位置（下文给方案）。

你在 click 事件里“额外插了一刀”

比如有类似代码：

const handleClick = () => {
  focusBlock(blockId); // 内部总是把光标放在行首 / 行尾
};


这种写法会覆盖浏览器原本根据点击坐标计算的 caret 位置，
所以用户点击中间，光标却被你代码强行改到行首或行尾，然后再被别的逻辑改回来 → 肉眼就看到一顿闪。

二、怎么“良好”解决，而不是打一辈子补丁？

核心原则一句话：

“用户鼠标点哪里，光标就在哪儿”这条链路，尽量完全交给浏览器；
我们只在“结构被改动（合并/拆分 block）”时接管 selection。

具体可以分三步处理。

Step 1：区分两种 selection：user vs command

给你的 selectionStore 加个来源字段：

type SelectionSource = 'user' | 'command';

type SelectionState =
  | { kind: 'none' }
  | { kind: 'caretAt'; blockId: string; offset: number; source: SelectionSource };


然后约定：

用户用鼠标点、用方向键移动等 → 不往 store 里写（或者写但标记为 user）；

只有在「拆分 block / 合并 block / 删除 block」这种命令操作时，
我们才设置 source: 'command'，告诉 effect：“这是我算好的位置，你去恢复”。

恢复 selection 的 effect，就只在 source === 'command' 时生效：

useEffect(() => {
  const sel = selectionStore.current;
  if (!sel || sel.kind !== 'caretAt' || sel.source !== 'command') return;

  requestAnimationFrame(() => {
    applySelection(sel);
  });
}, [blocksVersion]); // 只在结构变化后尝试恢复


这样：
纯粹的点击 / 光标移动就不会再被 effect 打断，扫来扫去的问题先砍掉一半。

Step 2：恢复光标时只做“一步到位”的 collapsed range

把之前那种「0..offset 再 collapse」的写法，换成一次性 collapsed：

function applySelection(sel: CaretAtSelection) {
  const node = getEditableTextNode(sel.blockId); // 拿到实际 text node
  if (!node) return;

  const selection = window.getSelection();
  if (!selection) return;

  // 可选优化：如果当前选区已经在同一位置，就什么都不做
  const current = selection.anchorNode === node && selection.anchorOffset === sel.offset;
  if (current) return;

  const range = document.createRange();
  range.setStart(node, sel.offset);
  range.collapse(true); // 直接折叠为插入点

  selection.removeAllRanges();
  selection.addRange(range);
}


要点：

只调用一次 setStart，不要先 setStart(..., 0) 再 setEnd(..., offset)；

使用 collapse(true) 折叠成一个 caret，而不是先构造选中区域；

可选：在设之前比对当前 selection，如果已经在目标位置，直接返回，避免无谓闪烁。

这样就不会出现那种“高亮从左往右扫一遍再消失”的视觉了。

Step 3：减少/取消 onClick 里对 selection 的干预

检查你所有跟 block 相关的点击逻辑，大概率能看到类似：

onClick={() => focusBlock(blockId)}

onMouseDown 里 preventDefault() 然后自己设置光标

处理建议：

对于包裹 contentEditable 的壳（shell）

如果点击 shell 也会进入编辑模式，但里面还有真正的 div[contentEditable]，

你可以在 onMouseDown 里简单地 innerEditable.focus()，不要自己算 caret，

不要 preventDefault，让浏览器根据点击位置决定光标。

只有在“点击 wrapper 但不在文字上”的区域，才需要自算 caret

比如：点在左侧空白区域，希望光标跳到行尾；

这时候用 caretRangeFromPoint(e.clientX, e.clientY) / caretPositionFromPoint 做一次：

const range =
  document.caretRangeFromPoint?.(e.clientX, e.clientY) ??
  caretFromPointPolyfill(e.clientX, e.clientY);

if (range) {
  const sel = window.getSelection();
  sel?.removeAllRanges();
  sel?.addRange(range);
}


仍然是“一步到位”的 collapsed range。

保证在 mousedown → mouseup 这段时间不要触发不必要的重渲染

比如：点击时不要立刻 setState({ selectedBlockId }) 触发一大坨 UI 改变，
可以延后到 mouseup，或者用 requestAnimationFrame 做“点击结束后”的状态更新，
这样浏览器原生的点击选区就不会被中途打断。

小结一下给你一个“标准动作”

当你遇到「光标看起来扫来扫去 / 闪来闪去」时，可以按这套 checklist 检查：

有没有 effect 在每次 block 更新后强制重放 selection？

有的话，只让它在 source === 'command' 时跑。

恢复 selection 的代码是不是在制造“0..offset 的临时选区”？

改成直接 range.setStart(node, offset); range.collapse(true);。

onClick / onMouseDown 里有没有做多余的 focus/selection 操作？

能交给浏览器的就交给浏览器，必要时只做一次“一步到位”的 range 设置。

做到这三点，
点击任意一行时你看到的应该是：光标瞬间出现在目标位置，没有那条“扫过去”的视觉动画，
真正有动画的，只剩你自愿加的那种漂亮的 hover/focus 效果，而不是 selection 在那里跑马拉松。


/////////////////////////////////////////////////////////////////////////////

三、执行记录（2025-12-02）

- [x] Step 1 · selectionStore 区分 command intent
  `frontend/src/modules/book-editor/model/selectionStore.ts` 增加 `source:'command'`、token clamp 以及 `resolveIntentOffset`；SelectionManager 订阅只在 command intent 上运行，并在成功调用 `handle.setCaretOffset` 或检测到 DOM caret 已命中后立即 `consume(intent.token)`，杜绝多次回放。
- [x] Step 2 · collapsed range + offset 比对
  `frontend/src/modules/book-editor/ui/BlockEditorCore.tsx` 重写 `placeCaretAtOffset`：text node walker + 空节点兜底 + `range.setStart + collapse(true)` 一步到位；同时暴露 `getCaretOffset` 供 SelectionManager 做幂等检查。
- [x] Step 3 · 点击链路最小化
  `frontend/src/modules/book-editor/ui/BlockItem.tsx` 保留 `focusCaretFromPoint` 只处理 wrapper 空白点击；常规 contentEditable 点击完全交给浏览器，避免 preventDefault/focusAtStart 重新触发 sweep。

四、验证与记录

- 静态守卫：`npx next lint --file src/modules/book-editor/ui/BlockEditorCore.tsx --file src/modules/book-editor/model/selectionStore.ts` ✅（2025-12-02）。
- 手动验证（Book Blocks 页面）：
  - 鼠标点击段落/标题任意位置，caret 立即落点且无“行首→目标”动画。
  - 执行 `BlockCommands.createBlock({selectionEdge:'start'})` 后，新块光标在行首闪烁，随后手动点击不会被命令重放覆盖。
  - Backspace 删除空段 → caret 稳定回到 fallback block 末尾。
- 待持续观察：跨浏览器（Edge/Firefox）下 `caretRangeFromPoint` 兼容性已经通过 helper 兜底，但仍需在多端 QA 走一次通用脚本。