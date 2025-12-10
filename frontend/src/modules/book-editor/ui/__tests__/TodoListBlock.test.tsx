import React, { act } from 'react';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import type { TodoListBlockContent } from '@/entities/block';
import { TodoListEditor } from '../TodoListBlock';
import type { KeyboardAction, KeyboardIntent } from '../../model/keyboardDecider';

const paragraphInstances: Array<{
  blockId: string;
  onKeyboardDecision?: (payload: { intent: KeyboardIntent; decision: KeyboardAction }) => boolean | void;
  getKeyboardContext?: (intent: KeyboardIntent) => unknown;
}> = [];

vi.mock('../ParagraphEditor', () => {
  return {
    ParagraphEditor: (props: any) => {
      paragraphInstances.push(props);
      return null;
    },
  };
});

const originalRaf = globalThis.requestAnimationFrame;
const originalCaf = globalThis.cancelAnimationFrame;

const ensureRaf = () => {
  if (!globalThis.requestAnimationFrame) {
    globalThis.requestAnimationFrame = ((cb: FrameRequestCallback) => window.setTimeout(() => cb(Date.now()), 0)) as any;
  }
  if (!globalThis.cancelAnimationFrame) {
    globalThis.cancelAnimationFrame = ((id: number) => window.clearTimeout(id)) as any;
  }
};

const editorPropsFor = (blockId: string) => {
  const matches = paragraphInstances.filter((props) => props.blockId === blockId);
  if (matches.length === 0) {
    throw new Error(`No ParagraphEditor captured for ${blockId}`);
  }
  return matches[matches.length - 1];
};

describe('TodoListEditor keyboard handling', () => {
  let container: HTMLDivElement | null = null;
  let root: Root | null = null;

  beforeAll(() => {
    (globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
    ensureRaf();
  });

  afterAll(() => {
    globalThis.requestAnimationFrame = originalRaf;
    globalThis.cancelAnimationFrame = originalCaf;
  });

  beforeEach(() => {
    paragraphInstances.length = 0;
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
  });

  afterEach(() => {
    if (root) {
      act(() => root!.unmount());
      root = null;
    }
    if (container) {
      document.body.removeChild(container);
      container = null;
    }
    paragraphInstances.length = 0;
  });

  const renderTodo = (overrides: Partial<React.ComponentProps<typeof TodoListEditor>> = {}) => {
    const props: React.ComponentProps<typeof TodoListEditor> = {
      blockId: 'todo-block',
      content: { items: [{ id: 'todo-0', text: '' }] } as TodoListBlockContent,
      onChange: vi.fn(),
      onExitEdit: vi.fn(),
      onDeleteEmptyBlock: vi.fn(),
      onSoftBreak: vi.fn(),
      autoFocus: false,
      readOnly: false,
      onStartEdit: vi.fn(),
      onFocusPrev: vi.fn(),
      onFocusNext: vi.fn(),
      onCreateSiblingBlock: vi.fn(),
      ...overrides,
    };

    act(() => {
      root!.render(<TodoListEditor {...props} />);
    });

    return props;
  };

  it('removes a middle todo item when requested', () => {
    const onChange = vi.fn();
    renderTodo({
      content: { items: [{ id: 'a', text: 'alpha' }, { id: 'b', text: '' }, { id: 'c', text: 'omega' }] },
      onChange,
    });

    const middle = editorPropsFor('todo-block-b');

    act(() => {
      const handled = middle.onKeyboardDecision?.({ intent: 'backspace', decision: 'todo-remove-item' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual([
      { id: 'a', text: 'alpha' },
      { id: 'c', text: 'omega' },
    ]);
  });

  it('requires double enter to exit when entire todo list is empty', () => {
    const onChange = vi.fn();
    const onExitEdit = vi.fn();
    const onDeleteEmptyBlock = vi.fn();
    const onCreateSiblingBlock = vi.fn();
    const baseProps = renderTodo({
      content: { items: [{ id: 'solo', text: '' }] },
      onChange,
      onExitEdit,
      onDeleteEmptyBlock,
      onCreateSiblingBlock,
    });

    const first = editorPropsFor('todo-block-solo');

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'todo-exit' });
      expect(handled).toBe(true);
    });

    expect(onExitEdit).not.toHaveBeenCalled();
    expect(onDeleteEmptyBlock).not.toHaveBeenCalled();
    const interim = onChange.mock.calls.at(-1)?.[0];
    expect(interim?.items?.length).toBe(2);

    act(() => {
      root!.render(<TodoListEditor {...baseProps} content={interim} />);
    });

    const secondId = interim?.items?.[1]?.id;
    if (!secondId) {
      throw new Error('Inserted todo id missing');
    }
    const newest = editorPropsFor(`todo-block-${secondId}`);

    act(() => {
      const handled = newest.onKeyboardDecision?.({ intent: 'enter', decision: 'todo-exit' });
      expect(handled).toBe(true);
    });

    expect(onExitEdit).toHaveBeenCalledTimes(1);
    expect(onDeleteEmptyBlock).toHaveBeenCalledTimes(1);
    expect(onCreateSiblingBlock).not.toHaveBeenCalled();
  });

  it('exits immediately on backspace when entire todo list is empty', () => {
    const onExitEdit = vi.fn();
    const onDeleteEmptyBlock = vi.fn();
    const onCreateSiblingBlock = vi.fn();
    renderTodo({
      content: { items: [{ id: 'solo', text: '' }] },
      onExitEdit,
      onDeleteEmptyBlock,
      onCreateSiblingBlock,
    });

    const first = editorPropsFor('todo-block-solo');

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'backspace', decision: 'todo-exit' });
      expect(handled).toBe(true);
    });

    expect(onExitEdit).toHaveBeenCalledTimes(1);
    expect(onDeleteEmptyBlock).toHaveBeenCalledTimes(1);
    expect(onCreateSiblingBlock).not.toHaveBeenCalled();
  });

  it('continues adding todos when trailing item is empty but list has content', () => {
    const onChange = vi.fn();
    renderTodo({
      content: { items: [{ id: 'a', text: 'alpha' }, { id: 'b', text: '' }] },
      onChange,
    });

    const trailing = editorPropsFor('todo-block-b');

    act(() => {
      const handled = trailing.onKeyboardDecision?.({ intent: 'enter', decision: 'todo-insert-item' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items?.length).toBe(3);
  });

  it('treats newline-only todo items as empty for the exit guard', () => {
    const onChange = vi.fn();
    renderTodo({
      content: { items: [{ id: 'solo', text: '\n' }] },
      onChange,
    });

    const first = editorPropsFor('todo-block-solo');

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'todo-exit' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items?.length).toBe(2);
  });
});
