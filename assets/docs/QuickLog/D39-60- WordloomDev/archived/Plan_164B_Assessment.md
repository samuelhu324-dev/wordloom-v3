一、现在到底在乱什么？

根据你在 Plan_164A 里写的三类问题，大概是这几个层次在互相扯头发：

组件职责过胖 / 过杂

BlockEditorCore 里既管：

block 列表渲染；

selection 订阅；

focusIntent / queueRowFocus 处理；

以及各种 placeCaret、autoFocus、readOnly 切换、副作用……

于是函数之间互相闭包引用，稍微挪个顺序，就出现
ReferenceError: Cannot access 'placeCaret' before initialization
典型 TDZ（临时死区）+ hooks 依赖顺序地狱。

光标“第三稳定性”问题

你已经有两个“自治系统”：

focusIntentStore：pointer / keyboard / initial intent；

selectionStore / 旧的 setSelection 协议：曾经直接动 window.getSelection()。

Plan163 系列在往 “只认 focusIntentStore” 收口，但旧协议还残留部分路径，一旦某条旧路径在“intent 之后再偷偷 setSelection”，就会把 caret 抢回去，表现成：

点击 list 时先闪到首字母；

上下键时先跳一行再被拉回来；

偶尔出现“扫射”：光标先飞到开头，又回到目标行。

Copilot 抛的新方案

它建议：

把 Plan163C 的 intent 处理“推广到剩余的 inline editors”；

把新的 BlockEditorCaretIntent 事件接到 QuickLog 里，方便监控回归。

核心是对的（所有路径都走同一个 intent 管道），但它没有帮你收尾旧协议，也没有处理组件内部的 TDZ 结构问题，所以现在是“三套逻辑并存”，互相干扰。

再加上你新遇到的两个具体 bug：

list 点击只到首字母：说明 pointer 路径只传了 edge: 'start' 或 offset=0，而没有根据点击坐标算出真正的字符 offset。

“分组件还是不分组件”：直觉上觉得 BlockEditorCore 太大很容易炸，但一旦拆成多个 React 组件，selection 就要跨组件同步，反而更容易出鬼。

二、先给结论：拆“逻辑模块”，不拆“可视组件”

不要把 BlockEditorCore 拆成多个渲染组件（比如 ParagraphLayer、ListLayer 各自挂 DOM），那会把 selection 搞成多源。

保持 一个“真正可编辑 DOM 容器”组件（BlockEditorCore），只负责：

渲染；

把事件意图（intent）接进来；

调用一套稳定的“caret 控制器 API”。

把所有危险的东西——placeCaret、setSelectionRange、getOffsetFromPoint、autoFocus、副作用——统统搬到：

纯函数工具模块（不依赖 React）；

自定义 hooks（只往外暴露稳定方法，不再在组件体内互相闭包）。

这样你既不用改 UI 架构，又能把“爆炸点”集中到一两个小模块里，出了问题更好排查。

三、Plan 164B：BlockEditorCore 稳定化 + 列表点击精确定位

下面这份可以直接整理成 MD 给 Copilot，当作“实现脚手架”。

0. 约束与目标

唯一 caret owner

唯一允许修改 window.getSelection() / caret 的地方：BlockEditorCore 内部的 useBlockCaretController（新建）。

任何其他模块 不能直接 调 setSelection、removeAllRanges、placeCaret。

唯一 intent 通道

所有“我要移动 caret”的行为：键盘、鼠标、初始化、block 命令（插入/删除/合并）——统一走
announceFocusIntent({ kind: 'keyboard' | 'pointer' | 'initial', ... })。

旧的 selectionStore.requestSelectionEdge / setBaseAndExtent 只能作为“监听 DOM selection 变化”的被动通道，不再写回 DOM。

List/Todo/Paragraph 这些 inline editor

自己不做 selection 操作，仅负责：

编辑文本；

在点击/键盘时发 intent；

把 blockId 和 “点击对应的 offset” 传出去。

1. 抽出 caret DOM 工具模块

文件：frontend/src/modules/book-editor/model/caretDomUtils.ts

内容示例（交给 Copilot具体补完）：

export function getSelectionWithin(root: HTMLElement): Selection | null {
  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) return null;
  const range = sel.getRangeAt(0);
  if (!root.contains(range.startContainer)) return null;
  return sel;
}

export function placeCaretAtNodeOffset(root: HTMLElement, node: Node, offset: number) {
  const sel = window.getSelection();
  if (!sel) return;
  const range = document.createRange();
  range.setStart(node, offset);
  range.collapse(true);
  sel.removeAllRanges();
  sel.addRange(range);
}

export function getOffsetFromPoint(textEl: HTMLElement, clientX: number, clientY: number): number {
  const range = document.createRange();
  let offset = 0;
  const textNode = textEl.firstChild;
  if (!textNode || textNode.nodeType !== Node.TEXT_NODE) return 0;

  // 通过二分 / 线性扫描把点击点映射到字符偏移
  // 交给 Copilot 实现细节
  // ...
  return offset;
}


关键点：不引用 React，不引用 store，只干 DOM 光标数学。

2. 抽出 intent 应用模块 / hook

文件：frontend/src/modules/book-editor/model/useBlockCaretController.ts

大致结构：

export interface BlockCaretController {
  placeCaretByIntent(intent: FocusIntentPayload): void;
  placeCaretAtOffset(blockId: string, offset: number): void;
}

export function useBlockCaretController(
  rootRef: React.RefObject<HTMLDivElement>,
  focusIntentStore: FocusIntentStoreApi,
  selectionStore: SelectionStoreApi,
): BlockCaretController {
  // 订阅 focusIntentStore 的队列变化
  // 根据 intent.kind 决定调用 caretDomUtils 里的方法
  // 比如 keyboard: 根据 rowIndex + edge 选中行首/行尾
  // pointer: 根据 blockId + offset 放置
  // initial: 初始 block 的最后一行/某个安全位置

  // 这里统一处理“消耗 intent”“防抖”等逻辑

  return {
    placeCaretByIntent,
    placeCaretAtOffset,
  };
}


然后：

BlockEditorCore 里只做：

const rootRef = useRef<HTMLDivElement | null>(null);
const controller = useBlockCaretController(rootRef, focusIntentStore, selectionStore);


所有 useEffect 只依赖 controller 暴露的函数，不再直接引用内部 placeCaret，自然不会再有 “before initialization” 的 TDZ 问题。

3. 精简 BlockEditorCore 组件体

**目标：**组件本身只负责“胶水”：

建 refs / controller：

const editorRootRef = useRef<HTMLDivElement | null>(null);
const caretController = useBlockCaretController(editorRootRef, ...);


把 announceFocusIntent 传下去：

<ListBlock
  block={block}
  onPointerFocus={(offset) =>
    announceFocusIntent({ kind: 'pointer', blockId: block.id, offset })
  }
/>


插入一个 SlashMenu 等 UI（你之前已经在做）。

不再在组件体上写长达几十行的 placeCaret/setSelection 逻辑，也不再在多个 useEffect 之间互相闭包引用这些函数。

4. 修复 List/Todo 点击只到首字母的问题

ListBlock / TodoListBlock 内部：

在 item 的文本容器上挂 onMouseDown 或 onClick：

const handleItemMouseDown = (event: React.MouseEvent<HTMLDivElement>) => {
  if (!textRef.current) return;
  const offset = getOffsetFromPoint(textRef.current, event.clientX, event.clientY);
  props.onPointerFocus(offset);
};


onPointerFocus 往上到 BlockItem → BlockEditorCore，最终转成 intent：

onPointerFocus={(offset) => {
  announceFocusIntent({
    kind: 'pointer',
    blockId,
    offset,
  });
}}


useBlockCaretController 在收到 kind: 'pointer' 时，把 (blockId, offset) 映射到真实 DOM node + offset，然后用 caretDomUtils.placeCaretAtNodeOffset 放置。

这样点击不再一律 edge: 'start'，而是基于用户点击位置，光标自然落到对应字符。

5. 把 Plan163C 的 intent 流程推广到所有 inline editors

这部分跟 Copilot 的“Next steps”是一致的，但你要多做两件事：

列清单：
所有还存在“自己玩 selection”的地方，例如：

ParagraphEditor（编辑态）；

ParagraphDisplay 的点击；

ListEditor、TodoListEditor 内部；

任何 onClick 里直接调 document.getSelection().set... 的旧代码。

统一替换：

全部改成 announceFocusIntent(...) 或调用 caretController.placeCaretAtOffset；

彻底删除 / 封装掉 selectionStore.requestSelectionEdge 那些会写 DOM 的 API，只保留监听版。

可以在 RULES / ADR 里写一句硬规则：

“任何模块若需要移动 caret，只能通过 FocusIntent 或 BlockCaretController，不得直接调用 window.getSelection().set...。”

6. 监控与防回潮

QuickLog & Dashboard

按 Copilot 提示，把 BlockEditorCaretIntent 记录到 QuickLog；

简单几个字段：kind（pointer/keyboard/initial）、blockId、offset、source（List/Paragraph/Command）。

一旦有“intent 连发两次”或“pointer 后立刻被 keyboard 覆盖”，你就能从日志上看到。

代码层防线

在 selectionStore 那边加注释/类型限制：

只暴露订阅 selection 的 API；

把任何 setSelectionRange 类函数标成 deprecated 或直接删掉。

补一个简单 lint 或搜索脚本：

CI 里 grep window.getSelection()，只允许出现在 caretDomUtils.ts。

四、要写进 RULES / ADR 的关键词

为了让以后自己也看得懂，建议在新的 ADR（比如 ADR-164B）里写清三条硬约束：

Caret owner 单一原则

BlockEditorCore + useBlockCaretController 是唯一可以修改 DOM selection 的模块。

Intent first 原则

所有光标移动必须先产生 FocusIntent，再由 caretController 执行；子编辑器只发 intent，不直接操作 selection。

Pointer 精确 offset 原则

列表 / 段落点击必须计算真实 offset，不得使用硬编码 edge: 'start' 或 offset=0。

这样你后面继续 refactor / 扩展（比如表格、panel block）时，只要守住这三条，就不会再轻易回到“光标扫射”的老路。

总之：这版计划的核心是 统一入口 + 统一通道 + 单一 owner。
一旦你把 DOM selection 改写权收紧到一个 hook，其他地方都只能发 intent 或请求 offset，Copilot 再怎么“有创意”也只能在这条管道里出牌，光标的行为会稳定很多。

## 2025-12-04 回填

- D1/D2：`caretDomUtils` 与 `useBlockCaretController` 已 merge，BlockEditorCore 只依赖 controller 暴露的 `placeCaretByIntent / focusFromPoint / publishSnapshot`，组件内部不再声明多套 placeCaret。
- D3/D4：BlockEditorCore + BlockItem/List/Todo shell 仅传递 intent，所有 pointer offset 均取自 `getOffsetFromPoint`，并通过 `announceFocusIntent({kind:'pointer', blockId, offset, source})` 交由 controller 统一消费。
- 旧 selectionStore mutation API/`useSelectionManager` 已删除，测试/命令代码全部迁移到 intent；`npm run test -- caretDomUtils` 与常规端到端演练确认 list/todo 点击落点一致。
- D5/D6 在 Plan164C 中补完：selectionStore 入口会记录 `BlockEditorCaretIntent` QuickLog 事件，RULES/ADR/ESLint 也固化了“单一 owner + intent-only”约束，防止 Plan164B 的成果被回退。