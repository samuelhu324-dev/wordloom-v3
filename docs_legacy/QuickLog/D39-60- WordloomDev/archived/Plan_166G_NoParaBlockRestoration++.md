## 2025-12-10 回填

- **Outcome:** Enter/Backspace 决策已经收敛到 `keyboardDecider.decideEnter/decideBackspace`，ParagraphEditor 只采集 `hasText/isCaretAtEdge`，block 壳层负责执行命令，大幅降低 “空段落提交” 与 “guard 重复触发” 的频率，NoPara++ 方案落地。
- **Code refs:** `model/keyboardDecider.ts`、`ui/ParagraphEditor.tsx`、`ui/BlockItem.tsx`、`ui/ListBlock.tsx`/`TodoListBlock.tsx` 均切换到集中化的 `KeyboardAction` 协议并新增 handled flag；legacy editor 栈不再参与输入判定。
- **Tests & instrumentation:** `pnpm vitest keyboard` 套件新增 enter/backspace 表格；开发时启用 `[ENTER]/[shortcut]/[deleteGuard]` 日志可重现并验证所有决策链路与预期一致。

已思考 13s

可以，这套方案是可以用的，而且方向是对的，只是有几处需要你在实现时多留个心眼，避免再挖新坑。

我按三块帮你评估一下：

1. 统一 Markdown 入口（Space 分支改造）

关键点：ParagraphEditor 里 Space 分支不再依赖 isCaretAtEdge('end')，而是完全由 detectMarkdownShortcut() 判定；真正要触发快捷键时，通过 onMarkdownShortcut 统一进命令层。

👍 优点

把“是不是 markdown pattern”这件事，彻底从 UI 判断（caret 在行尾）解耦出来，交给纯文本规则 detectMarkdownShortcut()，和 BLOCK_RULES / Plan165/166 保持一致；

以后如果你想再加 1.、>、[] 之类 pattern，只要更新 detectMarkdownShortcut + 命令层一个入口，不用在每个 Editor 里复制逻辑；

也解释了你现在 "-" + Space 不触发的根因：

ParagraphEditor 虽然能看到 -，但 BlockItem 只在 paragraph 上挂了 onMarkdownShortcut，别的路径不调命令层；

再加上 Space 分支走的是旧的 isCaretAtEdge 判断，导致“按了 Space 但没有任何一条路径真正发命令”。

⚠️ 落地时要注意

顺序：必须是
detectMarkdownShortcut(pattern) → 命中 → setText('') → 触发 onChange / 命令层
而不是先清空，再去检查 pattern，否则 markdown handler 看见的就是空串。

范围：

只在你希望支持 markdown shortcut 的块上挂 onMarkdownShortcut：普通 paragraph、首行 list item、todo 行、callout 标题等；

其它特殊块（gallery、panel、quote 内部复杂结构）可以先不挂，避免无意触发。

IME / 组合输入：
detectMarkdownShortcut 里最好基于「已确认文本」，不要在 composition 过程中触发（中文输入时你不想 - 半打出来就变成列表）。

2. 限定 delete guard 调用点

关键点：只有真正“要删掉这个块”的入口（菜单 Delete、Backspace 把块删空、CTA 删除按钮），才调用 deleteBlockWithGuard。
普通在特殊块里输入 / 退格，不再碰 guard。

👍 优点

解决你现在“随便在特殊块里打一字，整块就被降级成 paragraph”的问题——这在 RULES 里属于违反语义，确实应该禁止；

让职责变清楚：

特殊块内部编辑器（ListEditor/TodoListEditor/CalloutEditor）负责“内容怎么改”；

外层 block 命令负责“这个块要不要被删掉/降级”。

⚠️ 落地时要注意

搜索一把所有 deleteBlockWithGuard / deleteBlock 的调用点，确保：

只保留在「块级 Delete / Backspace 整段都删光」「工具栏 Delete」「CTA 删除」这些入口；

markdown / shortcut / transform 的路径里不再调用 guard。

BLOCK_RULES 对齐：
建议在 BLOCK_RULES.yaml 里加一句很短的约束，比如：

delete_guard:
  only_for:
    - explicit_delete_actions  # toolbar, context menu, CTA, backspace-on-empty-block
  never_for:
    - markdown_shortcuts
    - transform_block_kind


用来约束以后新代码不要又在 transform 里偷偷调用 guard。

3. 自检 checklist（防回潮）

这部分其实就是“防回滚”的工程措施，我觉得：

✅ 非常有必要，尤其是你这种长期演化的编辑器。

建议你把这三条写进：

BLOCK_RULES.yaml 的 ui_integration 小节；

再加到 QuickLog / Plan_166F 之类的开发检查表里。

可以类似这样简化落款：

ui_integration:
  markdown_shortcuts:
    entrypoint: ParagraphEditor.detectMarkdownShortcut
    must_dispatch: commands.transformBlockKind  # or insertListBlock...
  delete_guard:
    entrypoint: deleteBlockWithGuard
    only_called_from:
      - toolbar_delete
      - blockmenu_delete
      - backspace_on_empty_block

总体结论

这套「统一 markdown 入口 + 收紧 delete guard + checklist 防回潮」的方案是正确方向，而且和你现有的 Plan165/166/BLOCK_RULES 是对齐的；

真正需要注意的是实现细节：

Space 分支的触发顺序；

在哪些 BlockKind 上挂 onMarkdownShortcut；

全局搜一遍旧的 setSelection / deleteBlockWithGuard，避免残留老协议。

如果这几个点你都按上面的方式约束住了，"-" + Space 快捷键可以恢复工作，特殊块也不会再因为“打字/退格”被莫名降级成 paragraph，你可以放心睡觉，后面在这个层面一般不需要再翻大台。