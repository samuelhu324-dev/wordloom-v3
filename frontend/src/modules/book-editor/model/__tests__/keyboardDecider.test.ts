import { describe, it, expect } from 'vitest';
import {
  decideKeyboardAction,
  type ParagraphKeyboardContext,
  type ListKeyboardContext,
  type TodoKeyboardContext,
} from '../keyboardDecider';

const makeParagraphCtx = (overrides: Partial<ParagraphKeyboardContext> = {}): ParagraphKeyboardContext => ({
  blockKind: 'paragraph',
  isBlockEmpty: true,
  hasInlineText: false,
  caretAtStart: true,
  caretAtEnd: true,
  ...overrides,
});

const makeListCtx = (overrides: Partial<ListKeyboardContext> = {}): ListKeyboardContext => ({
  kind: 'list-item',
  listKind: 'bulleted_list',
  isItemEmpty: true,
  isFirstItem: true,
  isLastItem: true,
  allItemsEmpty: true,
  ...overrides,
});

const makeTodoCtx = (overrides: Partial<TodoKeyboardContext> = {}): TodoKeyboardContext => ({
  kind: 'todo-item',
  isItemEmpty: true,
  isFirstItem: false,
  isLastItem: true,
  allItemsEmpty: false,
  ...overrides,
});

describe('decideKeyboardAction', () => {
  it('creates new paragraph below when empty caret at end', () => {
    const action = decideKeyboardAction('enter', makeParagraphCtx());
    expect(action).toBe('create-below');
  });

  it('splits heading when it has inline text', () => {
    const action = decideKeyboardAction(
      'enter',
      makeParagraphCtx({ blockKind: 'heading', isBlockEmpty: false, hasInlineText: true }),
    );
    expect(action).toBe('split');
  });

  it('allows empty paragraph exit when override flag present', () => {
    const action = decideKeyboardAction('enter', makeParagraphCtx({ preferExitForLonelyEmpty: true }));
    expect(action).toBe('exit-edit');
  });

  it('ignores override when caret not covering entire block', () => {
    const action = decideKeyboardAction(
      'enter',
      makeParagraphCtx({ preferExitForLonelyEmpty: true, caretAtEnd: false, caretAtStart: true }),
    );
    expect(action).toBe('create-below');
  });

  it('returns noop for unsupported block kinds', () => {
    const action = decideKeyboardAction('enter', makeParagraphCtx({ blockKind: 'bulleted_list' }));
    expect(action).toBe('noop');
  });

  it('deletes paragraph block when backspace on empty start', () => {
    const action = decideKeyboardAction('backspace', makeParagraphCtx());
    expect(action).toBe('delete-block');
  });

  it('keeps paragraph when backspace but not at start', () => {
    const action = decideKeyboardAction('backspace', makeParagraphCtx({ caretAtStart: false }));
    expect(action).toBe('noop');
  });

  it('inserts a new list item when current item has text', () => {
    const action = decideKeyboardAction('enter', makeListCtx({ isItemEmpty: false }));
    expect(action).toBe('list-insert-item');
  });

  it('exits list when every item is empty', () => {
    const action = decideKeyboardAction('enter', makeListCtx({ allItemsEmpty: true }));
    expect(action).toBe('list-exit');
  });

  it('continues adding list items when last item is empty but others are not', () => {
    const action = decideKeyboardAction(
      'enter',
      makeListCtx({ allItemsEmpty: false, isLastItem: true, isItemEmpty: true, isFirstItem: false }),
    );
    expect(action).toBe('list-insert-item');
  });

  it('removes list item when empty and not last', () => {
    const action = decideKeyboardAction(
      'enter',
      makeListCtx({ isItemEmpty: true, isLastItem: false, allItemsEmpty: false }),
    );
    expect(action).toBe('list-remove-item');
  });

  it('uses backspace to exit list when first item empty', () => {
    const action = decideKeyboardAction('backspace', makeListCtx({ isItemEmpty: true, isFirstItem: true }));
    expect(action).toBe('list-exit');
  });

  it('inserts todo item when row has content', () => {
    const action = decideKeyboardAction(
      'enter',
      makeTodoCtx({ isItemEmpty: false }),
    );
    expect(action).toBe('todo-insert-item');
  });

  it('exits todo list when every item is empty', () => {
    const action = decideKeyboardAction(
      'enter',
      makeTodoCtx({ isItemEmpty: true, allItemsEmpty: true, isFirstItem: true, isLastItem: true }),
    );
    expect(action).toBe('todo-exit');
  });

  it('continues inserting when trailing todo is empty but list still has content', () => {
    const action = decideKeyboardAction(
      'enter',
      makeTodoCtx({ isItemEmpty: true, isLastItem: true, isFirstItem: false, allItemsEmpty: false }),
    );
    expect(action).toBe('todo-insert-item');
  });

  it('removes intermediate todo item when empty', () => {
    const action = decideKeyboardAction(
      'enter',
      makeTodoCtx({ isItemEmpty: true, isLastItem: false, isFirstItem: false, allItemsEmpty: false }),
    );
    expect(action).toBe('todo-remove-item');
  });

  it('exits todo block on backspace when entire list is empty', () => {
    const action = decideKeyboardAction(
      'backspace',
      makeTodoCtx({ isItemEmpty: true, isFirstItem: true, isLastItem: true, allItemsEmpty: true }),
    );
    expect(action).toBe('todo-exit');
  });

  it('exits todo block on backspace at first empty item even when others exist', () => {
    const action = decideKeyboardAction(
      'backspace',
      makeTodoCtx({ isItemEmpty: true, isFirstItem: true, isLastItem: false, allItemsEmpty: false }),
    );
    expect(action).toBe('todo-exit');
  });

  it('removes todo item on backspace when empty in the middle', () => {
    const action = decideKeyboardAction(
      'backspace',
      makeTodoCtx({ isItemEmpty: true, isFirstItem: false, isLastItem: false, allItemsEmpty: false }),
    );
    expect(action).toBe('todo-remove-item');
  });

  it('keeps todo item on backspace when it has content', () => {
    const action = decideKeyboardAction('backspace', makeTodoCtx({ isItemEmpty: false }));
    expect(action).toBe('noop');
  });
});
