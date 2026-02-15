好，那我们把刚才那套“删特殊块 → 降级为普通段落 + 至少保留一个基础段”写成可以直接丢给 Copilot 的技术计划。

下面这份你可以原样丢到 QuickLog / Plan_XXX 里，然后在对应文件开 Copilot。

Plan 165A：Base Paragraph Fallback（特殊块删除统一降级段落）

目标

文档始终至少有一个基础段落 block（kind: 'paragraph'）。

删除 / 退格 Quote / List / Todo / Panel 等“特殊块”时：

优先降级为普通段落，保留文本与 caret；

仅在不是最后一个 block 且内容为空时，才允许真正删除。

所有删除入口（Backspace、Delete、菜单“删除块”）都走同一套命令，不再各写一份 if/else。

1. 约定：哪些是“基础块 / 特殊块”

在 block 模型层（例如 frontend/src/modules/book-editor/model/blocks.ts 或类似位置）增加一个统一判断：

export type BlockKind =
  | 'paragraph'
  | 'heading'
  | 'todo'
  | 'bullet_list'
  | 'numbered_list'
  | 'quote'
  | 'callout'
  | 'panel'
  // ...

export const BASE_BLOCK_KIND: BlockKind = 'paragraph';

export function isSpecialBlock(kind: BlockKind): boolean {
  return (
    kind === 'todo' ||
    kind === 'bullet_list' ||
    kind === 'numbered_list' ||
    kind === 'quote' ||
    kind === 'callout' ||
    kind === 'panel'
    // 后续新增特殊块时，也放进来
  );
}


约定：基础块只有一个：paragraph；
其它全部视为“套了语义/外观皮肤的特殊 block”。

2. 新增统一“变更 block 类型”的命令

在命令层（例如 frontend/src/modules/book-editor/model/blockCommands.ts）添加一个通用的 transform：

export function transformBlockKind(
  editor: EditorState,
  blockId: string,
  newKind: BlockKind,
): EditorState {
  return updateBlock(editor, blockId, (block) => ({
    ...block,
    kind: newKind,
    // 如果不同 kind 有不同的 payload，可以在这里做 reset/normalize
  }));
}


后续所有：

Quote → Paragraph

List Item → Paragraph

Todo → Paragraph

全部走这条命令，方便做 undo / redo。

3. 核心守卫：ensureAtLeastOneBaseParagraph

在相同命令层实现一个统一的“删除守卫”，让所有删除都走它：

interface DeleteBlockOptions {
  /** 删除的是哪个 block */
  blockId: string;
  /** 删除时是否允许将最后一个特殊块降级为段落 */
  downgradeSpecialToBase?: boolean;
}

export function deleteBlockWithGuard(
  editor: EditorState,
  options: DeleteBlockOptions,
): EditorState {
  const { blockId, downgradeSpecialToBase = true } = options;
  const blocks = editor.blocks;
  const index = blocks.findIndex((b) => b.id === blockId);
  if (index === -1) return editor;

  const block = blocks[index];

  // 1) 文档只有一个 block 的情况：强制保留为基础段落
  if (blocks.length === 1) {
    // 如果已经是基础段落，只清空文本
    if (!isSpecialBlock(block.kind)) {
      return updateBlock(editor, blockId, (b) => ({
        ...b,
        text: '',
        // 其它 payload 重置
      }));
    }

    // 如果是特殊块 → 降级为基础段
    if (downgradeSpecialToBase) {
      return transformBlockKind(editor, blockId, BASE_BLOCK_KIND);
    }

    // 不允许任何真正删除
    return editor;
  }

  // 2) 文档有多个 block 的情况：
  // 2.1 空内容 & 非最后一个 → 可以删掉
  const isEmpty =
    (block.text ?? '').trim().length === 0 &&
    !hasMeaningfulChildren(block); // 如果有子块/列表项可以自己定义判断

  if (isEmpty && !isLastBlockInDocument(editor, blockId)) {
    return removeBlock(editor, blockId);
  }

  // 2.2 有内容：优先考虑“降级为基础块”
  if (isSpecialBlock(block.kind) && downgradeSpecialToBase) {
    return transformBlockKind(editor, blockId, BASE_BLOCK_KIND);
  }

  // 2.3 其它情况（普通段落、标题等）：由调用方决定，默认可以删除
  return removeBlock(editor, blockId);
}


辅助函数可以一起给 Copilot 生成：

function isLastBlockInDocument(editor: EditorState, blockId: string): boolean {
  const blocks = editor.blocks;
  return blocks.length > 0 && blocks[blocks.length - 1]?.id === blockId;
}

function hasMeaningfulChildren(block: Block): boolean {
  // TODO: 如果将来有嵌套子块，可以在这里判断
  return false;
}


这个函数就是整个“删特殊块 → 降级为 paragraph + 至少留一个基础段”的核心。
所有 Backspace / Delete / 菜单“删除块”只要改成调用它，行为就统一了。

4. 把 UI 层 Backspace / Delete 全部接到这个命令

以 BlockItem.tsx / ParagraphEditor.tsx 为例（路径按你仓库实际路径替换）：

4.1 BlockItem 里统一删除入口
const commands = useBlockCommands(); // 内部封装调用 deleteBlockWithGuard

const handleDeleteBlock = React.useCallback(() => {
  commands.deleteBlockWithGuard(block.id, { downgradeSpecialToBase: true });
}, [commands, block.id]);


useBlockCommands 里实现：

function useBlockCommands() {
  const [editor, setEditor] = useEditorState();

  const deleteBlockWithGuardCmd = React.useCallback(
    (blockId: string, opts?: { downgradeSpecialToBase?: boolean }) => {
      setEditor((prev) =>
        deleteBlockWithGuard(prev, {
          blockId,
          downgradeSpecialToBase: opts?.downgradeSpecialToBase ?? true,
        }),
      );
    },
    [setEditor],
  );

  return {
    deleteBlockWithGuard: deleteBlockWithGuardCmd,
    // ...其他命令
  };
}

4.2 Paragraph / List / Todo 的键盘逻辑调用统一删除

在 ParagraphEditor 等组件的 onKeyDown 中，把原来各种手写的“如果空就 deleteBlock(...) / transform(...)”改成只调 handleDeleteBlock：

const handleKeyDown = (event: React.KeyboardEvent) => {
  // Backspace at start of block:
  if (event.key === 'Backspace' && isCaretAtStart()) {
    event.preventDefault();
    onRequestDeleteBlock?.(); // BlockItem 传进来的 handleDeleteBlock
    return;
  }

  // Delete at end of block:
  if (event.key === 'Delete' && isCaretAtEnd()) {
    event.preventDefault();
    onRequestDeleteBlock?.();
    return;
  }

  // 其它快捷键逻辑...
};


这样，所有键盘触发的“删块”入口都走到了 deleteBlockWithGuard，不会再出现 Quote / List / Panel 每种写一份 if / else 的情况。

5. Slash 菜单 / 上下文菜单里的“删除块”也接到同一命令

Slash 菜单 item：

{
  id: 'delete-block',
  label: '删除块',
  onSelect: (ctx) => {
    commands.deleteBlockWithGuard(ctx.blockId);
  },
}


右键菜单同理。

关键点：今后任何地方需要“删除当前块”，一律调 commands.deleteBlockWithGuard(blockId)，不要再直接改 editor.blocks。

6. RULES / ADR 里记录设计约束（给 Copilot 也能读）

在 VISUAL_RULES.yaml 或 BLOCK_RULES.yaml / ADR 里加一条规则（文字可以直接 copy+adjust）：

- id: RULE-Block-Base-Paragraph
  summary: 文档必须至少包含一个基础段落 block；删除特殊块时优先降级为段落
  details: |
    - Base block kind is `paragraph`.
    - All special blocks (quote, list, todo, callout, panel, ...) are treated as
      "skins" or semantic wrappers on top of a paragraph.
    - deleteBlockWithGuard MUST:
      - If the document only has one block:
        - If it's special: transform kind to `paragraph` (keep text).
        - If it's already `paragraph`: clear text instead of removing.
      - If the block is special and has non-empty text:
        - transform kind to `paragraph` instead of removing.
    - UI-level Backspace/Delete and menus must not bypass this guard.

7. 自测 Checklist

给 Copilot 之后，你手测时重点过这些场景：

文档只有一个 Quote / Todo / List：

Backspace 删除壳 → 变成普通 paragraph，文字还在；

再 Backspace 清空文字 → 只变成空段落，不会把唯一块删没。

文档有多个 block：

中间的 Quote block 文本清空后 Backspace：

如果不是最后一个 block → 整块可被删除；

尾部的 Todo block 文本清空后 Backspace：

如果是最后一个 block → 只保留一个空段落（kind=paragraph）。

Slash 菜单 / 右键菜单“删除块”：

行为跟键盘 Backspace 一致，不会出现“菜单删干净，键盘却只是降级”的分裂情况。

你可以把上面这一整段当成 Plan_165A_BaseParagraphFallback.md 扔进仓库，然后在：

blockCommands.ts

BlockItem.tsx

ParagraphEditor.tsx

TodoListEditor.tsx / ListEditor.tsx

里用 Copilot 让它按“deleteBlockWithGuard”这条路线 refactor 现有逻辑。