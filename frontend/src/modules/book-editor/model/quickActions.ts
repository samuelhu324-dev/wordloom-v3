import type { BlockKind } from '@/entities/block';
import type { MessageKey } from '@/i18n/I18nContext';

export type QuickInsertBehavior = 'transform' | 'insert-below';
export type TranslateFn = (key: MessageKey, vars?: Record<string, string | number>) => string;

export interface QuickInsertAction {
  id: string;
  label: string;
  hint: string;
  kind: BlockKind;
  behavior: QuickInsertBehavior;
}

interface QuickInsertActionDefinition {
  id: string;
  labelKey: MessageKey;
  hintKey: MessageKey;
  kind: BlockKind;
  behavior: QuickInsertBehavior;
}

const QUICK_INSERT_ACTION_DEFS: QuickInsertActionDefinition[] = [
  {
    id: 'todo',
    labelKey: 'books.blocks.editor.commands.todo.label',
    hintKey: 'books.blocks.editor.commands.todo.hint',
    kind: 'todo_list',
    behavior: 'transform',
  },
  {
    id: 'bulleted-list',
    labelKey: 'books.blocks.editor.commands.bulletedList.label',
    hintKey: 'books.blocks.editor.commands.bulletedList.hint',
    kind: 'bulleted_list',
    behavior: 'transform',
  },
  {
    id: 'numbered-list',
    labelKey: 'books.blocks.editor.commands.numberedList.label',
    hintKey: 'books.blocks.editor.commands.numberedList.hint',
    kind: 'numbered_list',
    behavior: 'transform',
  },
  {
    id: 'callout',
    labelKey: 'books.blocks.editor.commands.callout.label',
    hintKey: 'books.blocks.editor.commands.callout.hint',
    kind: 'callout',
    behavior: 'transform',
  },
  {
    id: 'quote',
    labelKey: 'books.blocks.editor.commands.quote.label',
    hintKey: 'books.blocks.editor.commands.quote.hint',
    kind: 'quote',
    behavior: 'transform',
  },
  {
    id: 'panel',
    labelKey: 'books.blocks.editor.commands.panel.label',
    hintKey: 'books.blocks.editor.commands.panel.hint',
    kind: 'panel',
    behavior: 'insert-below',
  },
];

export const buildQuickInsertActions = (t: TranslateFn): QuickInsertAction[] =>
  QUICK_INSERT_ACTION_DEFS.map(({ id, labelKey, hintKey, kind, behavior }) => ({
    id,
    label: t(labelKey),
    hint: t(hintKey),
    kind,
    behavior,
  }));

export const QUICK_INSERT_ACTION_IDS = QUICK_INSERT_ACTION_DEFS.map((action) => action.id);
