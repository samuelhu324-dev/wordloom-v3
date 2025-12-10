import type { BlockKind } from '@/entities/block';

export type KeyboardIntent = 'enter' | 'backspace';

export type KeyboardAction =
  | 'split'
  | 'create-below'
  | 'exit-edit'
  | 'delete-block'
  | 'list-insert-item'
  | 'list-remove-item'
  | 'list-exit'
  | 'todo-insert-item'
  | 'todo-remove-item'
  | 'todo-exit'
  | 'noop';

export interface ParagraphKeyboardContext {
  kind?: 'block';
  blockKind: BlockKind;
  isBlockEmpty: boolean;
  hasInlineText: boolean;
  caretAtStart: boolean;
  caretAtEnd: boolean;
  preferExitForLonelyEmpty?: boolean;
}

type ListKind = Extract<BlockKind, 'bulleted_list' | 'numbered_list'>;

export interface ListKeyboardContext {
  kind: 'list-item';
  listKind: ListKind;
  isItemEmpty: boolean;
  isFirstItem: boolean;
  isLastItem: boolean;
  allItemsEmpty: boolean;
}

export interface TodoKeyboardContext {
  kind: 'todo-item';
  isItemEmpty: boolean;
  isFirstItem: boolean;
  isLastItem: boolean;
  allItemsEmpty: boolean;
}

export type KeyboardContext = ParagraphKeyboardContext | ListKeyboardContext | TodoKeyboardContext;

export type KeyboardContextInput =
  | Pick<ParagraphKeyboardContext, 'blockKind' | 'isBlockEmpty' | 'preferExitForLonelyEmpty'>
  | (Omit<ListKeyboardContext, 'isItemEmpty'> & { isItemEmpty?: boolean })
  | (Omit<TodoKeyboardContext, 'isItemEmpty'> & { isItemEmpty?: boolean });

const PARAGRAPHISH_KINDS = new Set<BlockKind>(['paragraph', 'heading']);
const EMPTY_EXIT_OVERRIDE_KINDS = new Set<BlockKind>(['paragraph']);

export const decideKeyboardAction = (intent: KeyboardIntent, ctx: KeyboardContext): KeyboardAction => {
  if (ctx.kind === 'list-item') {
    return decideListAction(intent, ctx);
  }
  if (ctx.kind === 'todo-item') {
    return decideTodoAction(intent, ctx);
  }
  return decideParagraphAction(intent, ctx);
};

const decideParagraphAction = (intent: KeyboardIntent, ctx: ParagraphKeyboardContext): KeyboardAction => {
  if (!PARAGRAPHISH_KINDS.has(ctx.blockKind)) {
    return 'noop';
  }

  if (intent === 'backspace') {
    if (ctx.isBlockEmpty && ctx.caretAtStart) {
      return 'delete-block';
    }
    return 'noop';
  }

  if (!ctx.isBlockEmpty || ctx.hasInlineText) {
    return 'split';
  }

  if (
    ctx.preferExitForLonelyEmpty &&
    EMPTY_EXIT_OVERRIDE_KINDS.has(ctx.blockKind) &&
    ctx.caretAtStart &&
    ctx.caretAtEnd
  ) {
    return 'exit-edit';
  }

  return 'create-below';
};

const decideListAction = (intent: KeyboardIntent, ctx: ListKeyboardContext): KeyboardAction => {
  if (intent === 'enter') {
    if (!ctx.isItemEmpty) {
      return 'list-insert-item';
    }
    if (ctx.allItemsEmpty) {
      return 'list-exit';
    }
    if (ctx.isLastItem) {
      return 'list-insert-item';
    }
    return 'list-remove-item';
  }

  // backspace
  if (!ctx.isItemEmpty) {
    return 'noop';
  }
  if (ctx.allItemsEmpty || ctx.isFirstItem) {
    return 'list-exit';
  }
  return 'list-remove-item';
};

const decideTodoAction = (intent: KeyboardIntent, ctx: TodoKeyboardContext): KeyboardAction => {
  if (intent === 'enter') {
    if (!ctx.isItemEmpty) {
      return 'todo-insert-item';
    }
    if (ctx.allItemsEmpty) {
      return 'todo-exit';
    }
    if (ctx.isLastItem) {
      return 'todo-insert-item';
    }
    return 'todo-remove-item';
  }

  // backspace
  if (!ctx.isItemEmpty) {
    return 'noop';
  }
  if (ctx.allItemsEmpty || ctx.isFirstItem) {
    return 'todo-exit';
  }
  return 'todo-remove-item';
};
