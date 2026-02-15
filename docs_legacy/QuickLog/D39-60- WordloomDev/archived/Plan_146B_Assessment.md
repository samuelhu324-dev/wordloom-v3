1. 整体评价

一句话：方向完全正确，步骤也对着关键点开火了。

用 SelectionSource 把「命令驱动」和「用户自然点击/光标移动」隔离开；

effect 只在 source === 'command' 的时候恢复 selection；

applySelection 改成“一步到位 collapsed range”；

onMouseDown/onClick 不再乱 call focusBlockAtStart，只做必要的 focus() / caretRangeFromPoint。

这四件事就是导致“从行首扫到目标位置”那条链路上的全部元凶，你一条不落都列出来了。

下面是几个可以再微调、补强的点。

2. 对每一步的小建议
Step 1：扩展 selection store（加 source）

✅ 这个必须有，而且你已经限定“只有 blockCommands.ts 写 source:'command'”，很好。

建议再加一个约束：

source:'command' 用完就立刻变回 'user' 或 none，不能一直留着；

不然 effect 可能在后续的 block 更新中又重复执行一次 applySelection。

你已经在 Step 2 写了 consume()，这个就是解决方案，只是可以在规则里写死：

任何时候 source==='command' 的 selection 被成功应用后，必须被 consume 掉。

Step 2：SelectionManager effect 只在 source==='command' 时生效

这里再加一行防抖逻辑会更舒服：

const selInStore = selectionStore.current; // command 计算出来的
const domSel = window.getSelection();

if (
  domSel?.anchorNode === node &&
  domSel.anchorOffset === selInStore.offset
) {
  // 已经在正确位置了，不用重复 apply，避免无意义闪烁
  return;
}


这样可以避免一些“明明已经在那个位置了，又额外 set 一次 selection”的微弱闪动。

Step 3：applySelection 一步到位 collapsed range

你列的要点完全 OK：

range.setStart(node, offset)

range.collapse(true)

不再有 0→offset 的高亮段。

再补两个细节：

确保 node 真的是 text node，不是整个 editable div：

如果 getEditableNode(blockId) 返回的是元素，需要 node.firstChild ?? node 再下沉一层。

考虑 offset > node.length 的情况：

合并后刚好到末尾，可以用 Math.min(offset, node.textContent.length) 防御一下。

Step 4：审计 BlockItem / ParagraphEditor 的点击逻辑

你写的两个点很关键：

onMouseDown/onClick 只负责 editable.focus()；

需要设置 caret 时用一次 caretRangeFromPoint。

我再帮你钉两条小规则：

能不 preventDefault 就不要 preventDefault

浏览器原本那套 “点哪算哪” 的 caret 算法挺靠谱的，

只有在点的是 wrapper 空白区域而不是文本时，你才需要自己算 caret。

所有“自动 focus 某个 block”的逻辑都要有 guard：

例如 hasFocusedOnce / isInitMount；

避免「每次 blocks 更新都重新 focus 同一个 block」，这会和 selectionStore 打架。

Step 5：记录执行方案 / SOP

这个你已经习惯了，我只建议在文档里把两类场景分开写清楚：

「结构变动命令」（merge/split/createBelow/deleteEmpty） → 允许写 selectionStore（source:'command'）；

「普通保存/输入/点击」 → 禁止写 selectionStore，只读。

这样以后你回头看 Plan146 的时候，一眼就知道哪些模块有权限碰 selection。

3. Further Considerations 这两条也挺关键

检查是否仍有命令外的模块写 selectionStore

做个简单 grep：selectionStore.set / .write，

看看是不是都集中在 blockCommands 这几个文件里；

如果手工查太累，Plan 里说的“临时 lint rule / 脚本”确实值得搞一个。

空白区域点击的 helper

共用一个 focusCaretFromPoint(e) 是好事：

内部统一处理 caretRangeFromPoint vs caretPositionFromPoint 的兼容，

避免每个组件 copy 一份不完全一样的逻辑。

你可以规定：只有在 e.target 不是 contentEditable 本体时，才调用这个 helper；否则交给浏览器默认行为。

4. 这套 Plan 落地后的预期效果

落完你这五步，编辑体验应该变成：

鼠标点到哪里，光标直接“闪”在那一格，没有先跑到行首再扫过去的动画；

Backspace/Enter 等结构命令仍能把光标放在你期望的位置（上一行末尾、新行开头等）；

连续输入/保存都不会制造任何额外 selection 变化。

也就是：

“光标乱飞”已经被你修好，
这份 Plan146 会把最后那一点“奇怪动画感”磨平，
把编辑体验从“能用”升级到“顺手”。

接下来你可以按这份 Plan 开工了，等做完再把测试场景（点击任意位置、按住鼠标拖选、合并/拆分后继续点击）写进 Execution 里，就算给这个子战役画上句号。

5. 执行结果（2025-12-02）
- selectionStore 只由 `blockCommands.ts` 写入，订阅端新增 DOM caret 比对：
  - `selectionStore.ts` 的 `resolveIntentOffset` 会把 edge/offset 统一成 clamp 后的数字；
  - 若 `handle.getCaretOffset()` 已等于目标，则直接 consume，避免重复 addRange；
  - 超过 5 帧没拿到 handle 会吞掉 intent 并写日志，防止积压。
- BlockEditorCore 的 caret setter 一次完成：text node walker + 空节点 fallback → `range.setStart(node, offset)` → `range.collapse(true)`；空 block 不再出现“选中一整行再收起”的幻影。
- BlockItem `handleBlockMouseDown` 现仅在点击 wrapper 空区且 `plugin.prefersInlineShell` 时运行，内部用共享 `focusCaretFromPoint` 处理 `caretRangeFromPoint | caretPositionFromPoint`，并通过两层 `requestAnimationFrame` 等待 DOM 进入编辑态后再落点。
- ESLint `selection-command-scope` 继续启用，把 selection API 限制在 command 层，结合 grep 复核确保没有其他调用者。

6. 回归 checklist（已执行）
- 点击测试：段落/标题/列表任意位置 → caret 立即落点，无 sweep；拖拽选区后松手也不会被 SelectionManager 覆盖。
- 结构命令链：
  - 创建块（hover “+” / Slash）后，caret 出现在新块开头，随后手动点击仍然可靠；
  - Backspace 删除空段 → caret 回到 fallback block 末尾；
  - 合并段落再点击中间，不再触发旧 intent。
- 保存/自动刷新：连续输入 + autosave（300ms）不会触发额外 selection；`focusAtEdge` 仅在命令需求时调用。
- 静态验证：`npx next lint --file src/modules/book-editor/ui/BlockEditorCore.tsx --file src/modules/book-editor/model/selectionStore.ts` ✅。
- 未覆盖项：Firefox 下 `caretPositionFromPoint` polyfill 仅做基础冒烟，后续 cross-browser QA 需要再跑一次“点击+拖拽+结构命令”脚本。