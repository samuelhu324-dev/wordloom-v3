好，三份 RULES 我大概看完了，里面关于 Block Editor 的东西其实已经帮你“画好了边界和骨架”。你现在要做的是：把这些规则翻译成 Copilot 能执行的工程任务。

我先帮你定位+整理结构，然后给你一段可以直接丢给 Copilot 的英文任务说明。

一、先给你一个“定位图”：这个模块要长啥样

从 DDD_RULES / HEXAGONAL_RULES / VISUAL_RULES 里抽出来的结论：

这是前端的一个独立子模块（Authoring / BlockEditor），
只通过 HTTP DTO 跟后端打交道，Domain 不知道任何编辑器细节。
（对应 RULE_BLOCK_EDITOR_BOUNDARY）

Block 的数据契约：

后端 BlockDto / BlockResponse：{ id, kind, content, fractional_index, ... }

content 始终是字符串：

文本类 = 普通字符串或 JSON { text: "..." }

富结构 / 列表 / 表格 = JSON.stringify(...) 后的字符串

前端由 api.normalizeBlock() + parseBlockContent(kind, raw) 转成 BlockContent union。
（RULE_BLOCK_CONTENT_NORMALIZATION）

编辑器分层：

数据 / API 层：
features/block/api.ts, features/block/hooks.ts 负责 TanStack Query + Adapter。

BlockEditor 模块：
只处理：

Block 列表的展示 / 本地状态；

内联编辑；

创建 / 删除 / 重排；

debounce 保存；

具体 Block 类型渲染/编辑 通过插件注册：blockPlugins（Paragraph, Heading, Quote…）。
（Plugin Registry (blockPlugins)）

当前阶段范围（先做 Phase 0 + Phase 1 的子集）：

VISUAL_RULES 里的 block_editor.phases 说得很清楚：

phase_0_minimal：

只读 + 文本/标题渲染

稳定获取 block 列表

phase_1_editing：

内容编辑（Text/Heading）

300ms debounce 保存

简单保存状态：saving/saved/error

你现在做的就是：
Paragraph/Heading 的 inline 编辑 + 新建块 + 删除/恢复 + 基础 UI。
重排 / paperballs / rich blocks 可以先留钩子，之后再补。

二、建议的前端目录结构（给 Copilot 的“搭脚手架蓝图”）

在 frontend/src 下建议这样组织（你可以稍微调整命名，但整体思想不变）：

src/
  entities/
    block/
      types.ts          # BlockKind, BlockContent, Block DTO 类型（已有，可补充）
  features/
    block/
      api.ts            # HTTP 调用 + normalizeBlock() 适配器（已有/正在用）
      hooks.ts          # useBlocks, useCreateBlock, useUpdateBlock...（已有）
  modules/
    book-editor/
      index.ts          # 对外导出 BookEditorRoot
      model/
        editorState.ts  # （可选）本地选中 block id 等小状态
        keyboard.ts     # Enter / Backspace 行为封装（当前阶段）
        caret.ts        # selectionchange → caretRect（以后做）
      ui/
        BookEditorRoot.tsx   # 入口：接收 bookId，使用 useBlocks()，渲染 BlockList
        BlockList.tsx        # 渲染一个 block 列表
        BlockItem.tsx        # 包一块：展示+编辑+hover 工具条
        ParagraphDisplay.tsx # 段落展示
        HeadingDisplay.tsx   # 标题展示
        ParagraphEditor.tsx  # 段落编辑器（contentEditable）
        HeadingEditor.tsx    # 标题编辑器（contentEditable）
        InlineCreateBar.tsx  # 在最后一个块后面的“写点什么…”占位
        BlockToolbar.tsx     # hover 出来的 + / 🕒 / 🗑 等按钮（可以先简化）


关键点：

只有 BlockItem.tsx 内部使用 hooks（useUpdateBlock/useDeleteBlock），
BlockList 只是 map→组件，保证 hooks 顺序稳定（对齐 block_editor_inline_decisions）。

BlockEditor 模块不关心后端仓库、事务、events，
全部通过 features/block/hooks.ts 暴露的 mutation 完成。

三、Copilot 需要知道的“行为规范”

整理成几条 rule，让它在实现细节时不乱来：

数据来源 / 适配：

从 features/block/hooks.ts 里使用：

useBlocks(bookId) 获取列表（已分页就按 RULES 做）

useCreateBlockMutation()

useUpdateBlockMutation()

useDeleteBlockMutation() / useRestoreBlockMutation()（如果已有）

BlockList 收到的类型是已经 normalizeBlock() 过的 BlockViewModel，
里面有：id, kind, content: BlockContent, fractionalIndex, isDeleted, ...

BlockList / BlockItem 分工：

BlockList 只做：

遍历 blocks；

按 kind 选择对应编辑组件；

传入回调（onChange, onSoftDelete 等）。

BlockItem：

内部持有当前文本的本地 state；

处理 onChange / onBlur / onKeyDown；

调用 update mutation，并做 300ms debounce；

负责显示 “Saving / Saved / Error” 状态徽章。

编辑行为（当前阶段）：

Paragraph/Heading 使用 contentEditable 的 div 或 p：

onInput 同步 text；

onKeyDown：

Enter 默认：阻止浏览器 insertParagraph，改成：

如果当前块非空 → 结束当前块，调用 createBlock 在下方插入一个新的 paragraph；

如果当前块为空 → 视为“退出编辑”，不新建；

Shift+Enter → 在当前块中插入软换行（手动 Range + <br>，以后再做也可以先留 TODO）。

Backspace 在块开头且为空时，可以调用 deleteBlock（以后再补）。

正在输入法组合时（event.isComposing）不要阻止 Enter。

Debounce 规则：

onChange 更新本地 state；

300ms 内无输入 → 调用 update mutation；

onBlur 时立即 flush 一次。

UI / Hover 工具条：

Hover 显示右上角三个 icons：+ / 时间线 / 删除：

使用 opacity + transition，默认 0，hover 变 1；

不要改变文字布局（绝对定位在右上角）。

InlineCreateBar 在列表末尾：

显示一条浅灰条 + “写点什么…”；

点击后直接创建一个新的 paragraph block 并把光标聚焦进去。

与 RULES 对齐的限制：

不要在 BlockEditor 里引入 Slate/ProseMirror 等库；
只用 React + 原生 DOM API，保持纯前端实现。

不要在这个模块里硬编码后端 URL 或 fetch，
只调用 features/block/api.ts / hooks.ts。

未来 rich block / media block 用插件登记：
现在先留一个 blockPlugins 常量，里面只注册 "paragraph" 和 "heading"，接口设计成可以扩展。

四、可以直接丢给 Copilot 的英文任务说明（你复制整段就行）
You are working in the Wordloom frontend (Next.js 14 + TypeScript + TanStack Query).

Goal: implement the initial Block Editor module for Book pages, aligned with DDD_RULES.yaml, HEXAGONAL_RULES.yaml and VISUAL_RULES.yaml.

High-level constraints (from the RULES files):

- BlockEditor is a pure frontend module. It must NOT leak any editor implementation details (contentEditable, etc.) into the domain or backend. Communication with the backend only happens via Block DTOs (id, kind, content, fractional_index, ...).
- Block content is always transferred as a string. For simple text/heading blocks it can be plain text or JSON like { "text": "..." }. Complex blocks (table, list, etc.) will use JSON.stringify on the frontend. The adapter in features/block/api.ts is responsible for parsing raw API responses into a BlockContent union.
- The initial phase only needs inline editing for PARAGRAPH and HEADING blocks: fetch list, render, edit, create, soft delete, and basic save state. Reorder / paperballs / rich blocks will be implemented later.

Please scaffold the following module structure:

- src/modules/book-editor/
  - index.ts: export BookEditorRoot component.
  - model/
    - keyboard.ts: shared Enter/Backspace behavior for inline editors.
    - caret.ts (placeholder): selectionchange → caretRect (can be TODO for now).
  - ui/
    - BookEditorRoot.tsx: takes a bookId, uses `useBlocks(bookId)` to fetch blocks, renders BlockList.
    - BlockList.tsx: renders a list of blocks using BlockItem; no hooks directly here.
    - BlockItem.tsx: wraps a single block, holds local editing state, shows hover toolbar, calls mutations.
    - ParagraphDisplay.tsx / HeadingDisplay.tsx: read-only views.
    - ParagraphEditor.tsx / HeadingEditor.tsx: inline editable components for text and heading.
    - InlineCreateBar.tsx: "write something..." bar after the last block.
    - BlockToolbar.tsx: hover toolbar with buttons (+, timeline, delete).

Data access and adapters:

- Reuse the existing data layer in `features/block/api.ts` and `features/block/hooks.ts`.
- Use `useBlocks(bookId)` to load the block list. The hook should already return normalized BlockViewModel objects (id, kind, content, fractionalIndex, isDeleted, etc.) via `normalizeBlock()`.
- Use mutations from `hooks.ts`: `useCreateBlockMutation`, `useUpdateBlockMutation`, `useDeleteBlockMutation`, `useRestoreBlockMutation` (if they exist). BlockEditor must NOT do raw fetch calls.

Inline editing behavior (Phase 0/1):

- ParagraphEditor/HeadingEditor should use a contentEditable div or p. They receive `value: string`, `onChange(value)`, and `onSubmit()` callbacks from BlockItem.
- Implement `onInput` to sync the text back to BlockItem’s local state.
- Implement `onKeyDown` with the following rules:
  - Ignore events where `event.isComposing === true` (IME composition).
  - When `event.key === "Enter"`:
    - `event.preventDefault()` so the browser does not run the default `insertParagraph` behavior.
    - For now: call `props.onSubmit()` (BlockItem will create a new paragraph block below using the create mutation and focus it). If the current block is empty, you can treat Enter as "exit editing" without creating a new block.
  - When `event.key === "Enter" && event.shiftKey`:
    - Treat it as a soft line break (we can TODO a helper that inserts a `<br>` using Range APIs).
- Debounce save:
  - BlockItem keeps a `text` state.
  - Whenever text changes, start a 300ms debounce timer; when it fires, call the update mutation with the new content.
  - On blur, flush immediately (call update mutation if there are pending changes).
  - Show a small status badge (Saving / Saved / Error) based on the mutation status.

Component responsibilities:

- `BookEditorRoot` handles routing and passes `bookId` to hooks. It should not know about editor internals.
- `BlockList` maps blocks to `BlockItem` and handles empty / loading / error states.
- `BlockItem`:
  - Chooses the correct display/editor component based on `block.kind` ("paragraph" or "heading").
  - Manages local `text` state and debounce timer.
  - Calls update/create/delete mutations.
  - Renders a hover toolbar in the top-right corner (opacity 0 → 1 on hover) with:
    - "+" button (create block below, using create mutation).
    - clock button (opens timeline later – for now just TODO).
    - trash button (soft delete the block).
- `InlineCreateBar` renders after the last block, with a light gray bar and placeholder text ("写点什么..."). On click, it calls the create mutation to insert a new paragraph block at the end and focuses it.

Styling and UX notes:

- Use Tailwind utility classes where possible; keep the look consistent with the existing Book workspace (white card, subtle borders, medium line height).
- Hover toolbar icons must be positioned absolutely on the right side of the block, so they do not shift text layout.
- Do NOT introduce external rich-text libraries like Slate or ProseMirror. This phase must use plain React + DOM APIs.

Please generate the initial implementation files and keep the code strongly typed (TypeScript strict mode). Prefer small, composable components. Add TODO comments where later phases (reorder, paperballs, rich blocks, caret service) will attach.


你可以先让 Copilot按这个说明搭目录 + 生成骨架组件，然后我们再一起细化里面的关键文件（比如 ParagraphEditor 的 Enter 行为、BlockItem 的 debounce 逻辑）。这样做下来，既符合你三份 RULES 的约束，又不会一次性走到“ProseMirror 级别”的复杂度。