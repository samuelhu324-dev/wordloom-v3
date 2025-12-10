import type { KeyboardEvent } from 'react';

export interface InlineEditorKeymap {
  hasText: () => boolean;
  onSubmit: () => void;
  onSoftBreak?: () => void;
  onExitEdit: () => void;
  onDeleteEmptyBlock?: () => void;
}

/**
 * Shared keyboard behavior for inline editors.
 * Aligns with Plan126/Plan128: Enter creates a new block, Shift+Enter is a soft break,
 * Backspace on empty block requests deletion.
 */
export const handleInlineEditorKeyDown = (
  event: KeyboardEvent<HTMLElement>,
  bindings: InlineEditorKeymap
) => {
  const isComposing =
    // React does not surface `isComposing` on its KeyboardEvent type yet, so read from the DOM event
    (event as Partial<KeyboardEvent<HTMLElement> & { isComposing: boolean }>).isComposing ??
    event.nativeEvent?.isComposing;

  if (isComposing) {
    return;
  }

  if (event.key === 'Enter') {
    event.preventDefault();
    if (event.shiftKey) {
      bindings.onSoftBreak?.();
      return;
    }
    bindings.onSubmit();
    return;
  }

  if (event.key === 'Backspace') {
    if (!bindings.hasText()) {
      bindings.onDeleteEmptyBlock?.();
    }
  }
};
