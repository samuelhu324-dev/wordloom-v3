import React, { act } from 'react';
import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import { createRoot, type Root } from 'react-dom/client';
import type { ListBlockContent } from '@/entities/block';
import { ListEditor } from '../ListBlock';
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

vi.mock('@/shared/telemetry/blockEditorTelemetry', () => ({
  reportBlockEditorCaretIntent: vi.fn(),
}));

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

describe('ListEditor keyboard handling', () => {
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

  const renderList = (overrides: Partial<React.ComponentProps<typeof ListEditor>> = {}) => {
    const props: React.ComponentProps<typeof ListEditor> = {
      blockId: 'list-block',
      content: { items: ['first'] } as ListBlockContent,
      ordered: false,
      onChange: vi.fn(),
      onExitEdit: vi.fn(),
      onDeleteEmptyBlock: vi.fn(),
      onSoftBreak: vi.fn(),
      onStartEdit: vi.fn(),
      onFocusPrev: vi.fn(),
      onFocusNext: vi.fn(),
      onCreateSiblingBlock: vi.fn(),
      ...overrides,
    };

    act(() => {
      root!.render(<ListEditor {...props} />);
    });

    return props;
  };

  const latestEditorProps = (index: number) => {
    const suffix = `-item-${index}`;
    const matches = paragraphInstances.filter((props) => props.blockId.endsWith(suffix));
    if (matches.length === 0) {
      throw new Error(`No ParagraphEditor captured for index ${index}`);
    }
    return matches[matches.length - 1];
  };

  it('adds a list item when decision requests insertion', () => {
    const onChange = vi.fn();
    renderList({ content: { items: ['alpha'] }, onChange });
    const first = latestEditorProps(0);

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'list-insert-item' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual(['alpha', '']);
  });

  it('removes the current item when decision requests removal', () => {
    const onChange = vi.fn();
    renderList({ content: { items: ['', 'next'] }, onChange });
    const first = latestEditorProps(0);

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'list-remove-item' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual(['next']);
  });

  it('exits the list and keeps remaining items when backspace requests exit on the first empty entry', () => {
    const onChange = vi.fn();
    const onExitEdit = vi.fn();
    const onCreateSiblingBlock = vi.fn();
    renderList({ content: { items: ['', 'filled'] }, onChange, onExitEdit, onCreateSiblingBlock });
    const first = latestEditorProps(0);

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'backspace', decision: 'list-exit' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual(['filled']);
    expect(onExitEdit).toHaveBeenCalledTimes(1);
    expect(onCreateSiblingBlock).toHaveBeenCalledTimes(1);
  });

  it('keeps extending the list when the trailing item is empty but the list still has content', () => {
    const onChange = vi.fn();
    renderList({ content: { items: ['alpha', ''] }, onChange });
    const last = latestEditorProps(1);

    act(() => {
      const handled = last.onKeyboardDecision?.({ intent: 'enter', decision: 'list-insert-item' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual(['alpha', '', '']);
  });

  it('requires double enter to exit when entire list is empty', () => {
    const onExitEdit = vi.fn();
    const onCreateSiblingBlock = vi.fn();
    const onDeleteEmptyBlock = vi.fn();
    const onChange = vi.fn();
    const baseProps = renderList({ content: { items: [''] }, onExitEdit, onCreateSiblingBlock, onDeleteEmptyBlock, onChange });
    const first = latestEditorProps(0);

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'list-exit' });
      expect(handled).toBe(true);
    });

    expect(onExitEdit).not.toHaveBeenCalled();
    expect(onCreateSiblingBlock).not.toHaveBeenCalled();
    expect(onDeleteEmptyBlock).not.toHaveBeenCalled();
    const interim = onChange.mock.calls.at(-1)?.[0];
    expect(interim?.items).toEqual(['', '']);

    act(() => {
      root!.render(<ListEditor {...baseProps} content={{ items: interim.items }} />);
    });

    const newest = latestEditorProps(1);
    act(() => {
      const handled = newest.onKeyboardDecision?.({ intent: 'enter', decision: 'list-exit' });
      expect(handled).toBe(true);
    });

    expect(onExitEdit).toHaveBeenCalledTimes(1);
    expect(onCreateSiblingBlock).not.toHaveBeenCalled();
    expect(onDeleteEmptyBlock).toHaveBeenCalledTimes(1);
  });

  it('provides accurate enter context metadata per item', () => {
    renderList({ content: { items: ['one', 'two'] }, ordered: true });
    const first = latestEditorProps(0);
    const last = latestEditorProps(1);

    expect(first.getKeyboardContext?.('enter')).toEqual({
      kind: 'list-item',
      listKind: 'numbered_list',
      isFirstItem: true,
      isLastItem: false,
      allItemsEmpty: false,
    });

    expect(last.getKeyboardContext?.('enter')).toEqual({
      kind: 'list-item',
      listKind: 'numbered_list',
      isFirstItem: false,
      isLastItem: true,
      allItemsEmpty: false,
    });
  });

  it('treats newline-only list items as empty for pending exit guard', () => {
    const onChange = vi.fn();
    renderList({ content: { items: ['\n'] }, onChange });
    const first = latestEditorProps(0);

    act(() => {
      const handled = first.onKeyboardDecision?.({ intent: 'enter', decision: 'list-exit' });
      expect(handled).toBe(true);
    });

    const payload = onChange.mock.calls.at(-1)?.[0];
    expect(payload?.items).toEqual(['\n', '']);
  });
});
