一、为什么保存会把光标踢飞？

常见的几种“死亡连锁”，你现在很可能同时踩了两三个：

1. 保存触发了整行/整本 block 的重渲染

典型路径：

const handleChange = (text: string) => {
  updateBlock(blockId, text);   // 改全局 store
};


然后在上层：

const blocks = useStore(...);   // 每次 change 都返回新的 blocks 数组

return blocks.map(block => (
  <BlockItem key={block.id} ... />
));


再加上一些“贴心”的效果：

某个 useEffect 里，有类似：

// 有当前选中的 block，就自动 focus 到它（光标放开头）
useEffect(() => {
  if (selectedBlockId === block.id) {
    focusBlockAtStart(block.id);
  }
}, [selectedBlockId, block.id]);


于是你一敲字：

updateBlock ⇒ 整个 blocks 列表变对象；

React 重新渲染 BlockItem / ParagraphEditor；

某个 effect 看到“这是选中的 block”，就帮你调用 focusBlockAtStart；

光标毫无悬念回到行首，或者干脆回到第一行。

你这次修改以后“打两个字就跳首行”，高度符合这个模式：
每次 input 都触发一次保存 / 更新 store，间接触发“自动 focus 第一个 block”的逻辑。

2. 保存时重新写了 contentEditable 里的内容

另一条常见死亡路线：

// props.text 来自 store，每次保存都会更新
useEffect(() => {
  editableRef.current!.innerText = props.text;
}, [props.text]);


浏览器已经帮你把新键入的字符画出来了；

你又在 effect 里用 innerText = props.text 重刷一遍；

如果 props.text 比当前 DOM 版本落后一两拍，
光标就会被挤到行首 / 行尾 / 奇怪的位置。

3. 保存路径里偷偷写 selection

比如：

const handleSave = () => {
  updateBlock(blockId, text);
  selectionStore.set({ blockId, offset: 0 });  // “保存完就把光标放到开头”
};


或者 effect：

useEffect(() => {
  if (justSaved) {
    applySelectionAt(blockId, 0);
  }
}, [justSaved, blockId]);


这些东西和「command 触发的 selection 恢复」混在一起时，
就会出现你说的那种：怎么改都好像好一点，但又坏在别的地方。

二、怎么把“保存”从光标系统里彻底切出去？

给你一个硬规则版的方案：保存只负责“数据落地”，不改 DOM、不改 selection、不改 block 结构。具体可以这样做。

Step 1：把「编辑中的文本」从保存逻辑里拆出来

在 BlockEditorCore 内部：

function BlockEditorCore({ blockId, initialText, onDebouncedChange, onSave }) {
  const editableRef = useRef<HTMLDivElement | null>(null);
  const textRef = useRef(initialText);

  // 只在 blockId 变化时同步一次 initialText（比如切到别的 book）
  useEffect(() => {
    if (!editableRef.current) return;
    editableRef.current.innerText = initialText;
    textRef.current = initialText;
  }, [blockId, initialText]);

  const handleInput = useCallback((e: React.FormEvent<HTMLDivElement>) => {
    const value = (e.target as HTMLDivElement).innerText;
    textRef.current = value;
    onDebouncedChange?.(value);      // 去抖后同步给 store / autosave
  }, []);

  const handleSave = useCallback(() => {
    // 只把当前文本告诉上层，不自己动 selection、不动 DOM
    onSave?.(textRef.current);
  }, []);

  return (
    <div
      ref={editableRef}
      contentEditable
      suppressContentEditableWarning
      onInput={handleInput}
      // Enter / Ctrl+S 等触发 handleSave，但自身不改 key / 不改 DOM
    />
  );
}


上层接到 onDebouncedChange / onSave 后，只做数据上的事：

// debounced change -> 只更新 block.text，不改任何“当前选中 block”/“自动 focus”状态
updateBlockText(blockId, newText);

// save -> 调用 API / 写入本地 storage
persistBlock(blockId, newText);


注意两点：

BlockEditorCore 的 React key 必须只依赖 blockId，不因为“保存状态”变化而改变；

persistBlock 不要顺手去改「当前选中 blockId」之类的东西。

Step 2：把所有“自动 focus / 选中 block”从保存路径里拔掉

搜索代码里这些关键词：

selectionStore.set

focusBlock / focusBlockAtStart / focusFirstBlock

document.getSelection() / setSelectionRange / addRange

然后问自己一句：

这个调用是不是在「按 Enter/Backspace 合并/拆分块」以外的场景触发？

如果答案是“是”，就要怀疑它是不是在保存路径/普通输入路径里多嘴了。

硬限制可以写进 Plan / 规则里：

RULE-SEL-01：只有 command（split/merge/createBelow/deleteEmpty）允许写 selectionStore；

RULE-SEL-02：保存、自动同步、autosave 不得改 selection，只能改数据；

RULE-SEL-03：页面初始化时可以有一次“focus 第一块”的逻辑，但必须带 hasFocusedOnce 之类的 guard，避免每次 blocks 更新都重新跑。

例如：

const hasFocusedOnce = useRef(false);

useEffect(() => {
  if (!hasFocusedOnce.current && blocks.length > 0) {
    hasFocusedOnce.current = true;
    focusBlockAtStart(blocks[0].id);
  }
}, [blocks.length]);


而不是：

// ❌ 每次 blocks 变动都 focus 第一块
useEffect(() => {
  if (blocks.length > 0) {
    focusBlockAtStart(blocks[0].id);
  }
}, [blocks]);


后者配合“每次保存都新建 blocks 数组”，就是你现在的噩梦。

Step 3：做一个“小实验”确认是不是保存惹的祸

这个实验你可以自己马上做：

暂时把 onSave 里的所有逻辑注释掉，只保留最小版：

const handleSave = () => {
  console.log('SAVE (no-op)');
};


同时把任何跟保存状态有关的 useEffect 也注释掉（比如 useEffect([lastSavedAt])）。

再测试：

连续输入是否还会“两个字就跳首行”；

按 Ctrl+S（或你绑定的保存快捷键）后光标会不会乱跑。

如果：

注释掉保存逻辑后，一切都平稳了 → 说明问题 100% 在保存路径；

输入还是会跳 → 那就是前面说的“受控文本 + 频繁重渲染”问题，得再往上查 updateBlock/blocks.map/key。

这个实验的好处是：把“保存”和“输入”先物理隔离开来，你就不会在脑子里被两条链混淆。

三、给你一份“保存机制重构 checklist”

你接下来可以照着这几条一条条打勾：

 BlockEditorCore 内部：

保证只在 blockId 变化时重写 innerText；

普通输入仅更新 textRef + 去抖回调；

 onSave 只改数据 / 持久化，不改 selection，不改当前选中的 block；

 搜索全项目：保存相关的代码里不允许出现

focusBlock*

selectionStore.set*

getSelection().addRange 之类的调用；

 任何“自动 focus 第一行”的逻辑都加 hasFocusedOnce 标志，只在真正初始化时跑一次；

 确认 block 的 React key = block.id，跟“保存状态”完全无关。

做到这几条，你就会发现：

保存再也不会顺手把你扔回首行；

输入两个字就跳首行的症状要么直接消失，要么缩小到一个很明确的点（比如某个 effect 仍在乱动 selection），变得很好查。

你现在卡住的其实是**“保存、同步、光标”纠缠在一起**，
把保存从这团线里抽出来之后，剩下的 cursor bug 就会变成一个个可单杀的小怪，而不是一条三头龙了。

/////

保存机制修订计划（Plan147 × RULES 协同版）

目标与约束

符合 POLICY-BLOCK-PLAN142-AUTOSAVE-LOCAL（DDD_RULES）：保存仅更新 Block 数据，不触碰 selection / block 结构。
落实 block_editor_autosave_context_contract（HEXAGONAL_RULES）：BlockEditorContext 作为唯一实时源，UpdateBlockUseCase 只接收 {content}。
遵守 VISUAL_RULES 中 CURSOR-01~06：BlockEditorCore 统一 DOM、selection 只在 command 链触发，autosave 不得触发 refetch。

执行标记（2025-12-02）
- [x] 阶段 0 —— “no-op save” 对照实验 & hasFocusedOnce 审计（2025-10-28 完成，日志见 EverydayLog/2025-10-28）。
- [x] 阶段 1 —— Autosave 内核重构（2025-10-29 完成，关联提交 f1ff3b3）。
- [ ] 阶段 2 —— 状态源统一与 UndoManager 回放（计划中）。
- [ ] 阶段 3 —— 观测指标与回归防线（待 Stage2 验收后执行）。

阶段 0 · 基线验证

基于 Plan147 的“no-op save”实验，确认问题出在保存路径而非 BlockEditorCore 本体。
使用 hasFocusedOnce 哨兵审计所有“自动 focus” effect，确保只在首次挂载时执行，避免 blocks refetch 反复触发。
阶段 1 · Autosave 内核重构

BlockEditorCore 限定同步窗口
仅在 blockId 变化时重置 innerText，其余输入通过 textRef + onDebouncedChange 传出。
onSave 只回调文本；禁止在组件内写 selection 或触发外部 focus。
- 状态：✅ 2025-10-29 完成（BlockEditorCore.tsx 引入 blockVersionRef + clearDebounce 守卫，只在 blockId 变动时重写 DOM，彻底拔掉 initialValue diff 导致的光标跳动）。
useBlockAutosaveMutation 全面替换 useUpdateBlock
写入后调用 upsertRenderableBlock；杜绝 invalidateQueries(['blocks'])（已在前序代码落地）。
失败时仅回滚局部 block，保持 DOM 不变。
取消保存路径中的所有 selection store 写入
代码审计 selectionStore.*，保留 split/merge/delete/newBlock 的命令意图，删除 autosave/blur 回调里的 selection 写入。
对照 VISUAL_RULES CURSOR-04/05 将命令与保存彻底解耦。
- 状态：✅ 2025-10-29 完成（新增 ESLint 规则 selection-command-scope，禁止除 blockCommands 之外的模块 import selectionStore/requestSelectionEdge，失守即编译期报错，保证 selection intent 只在结构命令链出现）。
阶段 2 · 状态源统一与回放保障

BlockEditorContext 作为唯一渲染来源
reconcileRenderableBlocks 只在服务器数据与本地差异时更新对象，防止每次保存触发整表替换。
inline create/delete 命令全部通过 blockCommands 乐观更新后再调用 UseCase。
selection 恢复链路回归 command-only
BlockItem 仅在拆分/合并/删除空块前调用 requestSelectionEdge。
InlineCreateBar、handleCreateBelow 均通过 selectionEdge: 'start' 走统一入口。
UndoManager 对齐新状态源
Snapshot 读取 BlockEditorContext.blocks，确保撤销/重做不依赖旧的 React Query 缓存。
Push/Reset 流程遵守 POLICY-BLOCK-PLAN134-UNDO-CLIENT-ONLY，防止 undo 栈携带 selection 之外的数据。
阶段 3 · 观测与回归防线

记录：在 Plan147 QuickLog 中补充“保存机制矩阵”，列出 输入 → autosave → persist → selection 责任链。
监控：为 autosave mutation 添加计数与失败告警，确认没有 fallback to refetch。
验证：
单元测试覆盖 reconcileRenderableBlocks 的“本地编辑 vs 服务器刷新”场景。
Playwright/RTL 场景：连续输入、Ctrl+S、Backspace 删空块、Enter 新块，确保 caret 位置符合 VISUAL_RULES。
性能回归：确认去掉 invalidate 后，BlockList 不再出现整表刷新。
交付与文档同步

Plan147 文档补写“保存机制 Checklist”（已在原文末列出），并将 RULES 引用编号化，方便 QA 对照。
在 DDD/HEXAGONAL/VISUAL 三份 RULES 内追加此次改动的 changelog（已更新的条目需标注日期），确保后续评审有据可查。
执行完上述阶段，即可将保存逻辑彻底从光标系统解耦：输入 → DOM，保存 → 数据，selection → command intent，各自独立又通过 BLOCKEDITOR context 协调，满足 Plan147 与 RULES 的双重约束。