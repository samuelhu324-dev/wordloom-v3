import { describe, it, expect, vi } from 'vitest';
import type { KeyboardEvent } from 'react';
import { handleInlineEditorKeyDown } from '../keyboard';

type Bindings = Parameters<typeof handleInlineEditorKeyDown>[1];

type MutableKeyboardEvent = Partial<KeyboardEvent<HTMLElement>> & { preventDefault: () => void };

const createEvent = (overrides: Partial<MutableKeyboardEvent> = {}): KeyboardEvent<HTMLElement> => {
  return {
    key: 'Enter',
    shiftKey: false,
    isComposing: false,
    preventDefault: vi.fn(),
    ...overrides,
  } as KeyboardEvent<HTMLElement>;
};

describe('handleInlineEditorKeyDown', () => {
  const baseBindings = (): Bindings => ({
    hasText: () => true,
    onSubmit: vi.fn(),
    onExitEdit: vi.fn(),
  });

  it('submits block on Enter when has text', () => {
    const bindings = baseBindings();
    const event = createEvent({ key: 'Enter' });

    handleInlineEditorKeyDown(event, bindings);

    expect(bindings.onSubmit).toHaveBeenCalledTimes(1);
    expect(bindings.onExitEdit).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalledTimes(1);
  });

  it('still submits on Enter when empty', () => {
    const bindings: Bindings = {
      ...baseBindings(),
      hasText: () => false,
    };
    const event = createEvent({ key: 'Enter' });

    handleInlineEditorKeyDown(event, bindings);

    expect(bindings.onSubmit).toHaveBeenCalledTimes(1);
    expect(bindings.onExitEdit).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalledTimes(1);
  });

  it('inserts soft break on Shift+Enter when handler provided', () => {
    const onSoftBreak = vi.fn();
    const bindings: Bindings = {
      ...baseBindings(),
      onSoftBreak,
    };
    const event = createEvent({ key: 'Enter', shiftKey: true });

    handleInlineEditorKeyDown(event, bindings);

    expect(onSoftBreak).toHaveBeenCalledTimes(1);
    expect(bindings.onSubmit).not.toHaveBeenCalled();
    expect(event.preventDefault).toHaveBeenCalledTimes(1);
  });

  it('invokes delete callback on Backspace when empty', () => {
    const onDeleteEmptyBlock = vi.fn();
    const bindings: Bindings = {
      ...baseBindings(),
      hasText: () => false,
      onDeleteEmptyBlock,
    };
    const event = createEvent({ key: 'Backspace' });

    handleInlineEditorKeyDown(event, bindings);

    expect(onDeleteEmptyBlock).toHaveBeenCalledTimes(1);
    expect(event.preventDefault).not.toHaveBeenCalled();
  });
});
