'use client';

import React from 'react';
import styles from './bookEditor.module.css';
import { registerBlockEditorHandle, unregisterBlockEditorHandle } from '../model/editorRegistry';
import { announceFocusIntent } from '../model/selectionStore';
import { extractInlineTextFromEditable } from '../model/inlineText';
import { useBlockCaretController } from '../model/useBlockCaretController';

export type BlockEditorStartEditRequest =
  | { source: 'key'; key: string; shiftKey?: boolean }
  | { source: 'click' }
  | { source: 'focus' }
  | { source: 'pointer' };

export interface BlockEditorCoreHandle {
  getText: () => string;
  hasText: () => boolean;
  isCaretAtEdge: (edge: 'start' | 'end') => boolean;
  focusAtEdge: (edge: 'start' | 'end') => void;
  setCaretOffset: (offset: number) => void;
  setText: (next: string) => void;
  getCaretRect: () => DOMRect | null;
  getCaretOffset: () => number | null;
  focusFromPoint: (clientX: number, clientY: number) => void;
  getOffsetFromPoint: (clientX: number, clientY: number) => number | null;
}

export interface BlockEditorCoreProps extends React.HTMLAttributes<HTMLDivElement> {
  blockId: string;
  initialValue: string;
  autoFocus?: boolean;
  focusPosition?: 'start' | 'end';
  readOnly?: boolean;
  placeholder?: string;
  debounceMs?: number;
  onDebouncedChange?: (value: string) => void;
  onRequestStartEdit?: (request?: BlockEditorStartEditRequest) => void;
  onImmediateChange?: (value: string) => void;
}

const DEFAULT_DEBOUNCE_MS = 220;

const ZERO_WIDTH_PATTERN = /[\u00A0\u200B\uFEFF]/g;

const isTextEffectivelyEmpty = (value: string): boolean => {
  if (!value) {
    return true;
  }
  const normalized = value.replace(ZERO_WIDTH_PATTERN, '').trim();
  return normalized.length === 0;
};

export const BlockEditorCore = React.forwardRef<BlockEditorCoreHandle, BlockEditorCoreProps>((props, ref) => {
  const {
    blockId,
    initialValue,
    autoFocus,
    focusPosition,
    readOnly,
    placeholder,
    debounceMs = DEFAULT_DEBOUNCE_MS,
    onDebouncedChange,
    onImmediateChange,
    onRequestStartEdit,
    className,
    onKeyDown,
    onBlur,
    onFocus,
    onClick,
    ...rest
  } = props;

  const editableRef = React.useRef<HTMLDivElement | null>(null);
  const textRef = React.useRef(initialValue);
  const lastSyncedRef = React.useRef(initialValue);
  const debounceRef = React.useRef<number | null>(null);
  const [isEmpty, setIsEmpty] = React.useState(() => isTextEffectivelyEmpty(initialValue));
  const updateEmptyState = React.useCallback((nextValue: string) => {
    const nextEmpty = isTextEffectivelyEmpty(nextValue);
    setIsEmpty((prev) => (prev === nextEmpty ? prev : nextEmpty));
  }, []);

  const clearDebounce = React.useCallback(() => {
    if (debounceRef.current) {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = null;
    }
  }, []);

  const flushSync = React.useCallback(() => {
    if (!onDebouncedChange) {
      return;
    }
    clearDebounce();
    if (lastSyncedRef.current === textRef.current) {
      return;
    }
    lastSyncedRef.current = textRef.current;
    onDebouncedChange(textRef.current);
  }, [clearDebounce, onDebouncedChange]);

  const scheduleDebounce = React.useCallback(() => {
    if (!onDebouncedChange) {
      return;
    }
    clearDebounce();
    debounceRef.current = window.setTimeout(() => {
      debounceRef.current = null;
      flushSync();
    }, debounceMs);
  }, [clearDebounce, debounceMs, flushSync, onDebouncedChange]);

  React.useEffect(() => () => clearDebounce(), [clearDebounce]);

  const setTextContent = React.useCallback((next: string) => {
    textRef.current = next;
    updateEmptyState(next);
    if (editableRef.current && editableRef.current.textContent !== next) {
      editableRef.current.textContent = next;
    }
  }, [updateEmptyState]);

  const blockVersionRef = React.useRef<string | null>(null);

  const caretController = useBlockCaretController({
    blockId,
    editableRef,
    autoFocus,
    focusPosition,
    readOnly,
  });

  const {
    getCaretRect,
    getCaretOffset,
    isCaretAtEdge,
    placeCaretAtOffset,
    placeCaretAtEdge,
    focusFromPoint,
    getOffsetFromPoint,
    publishSelectionSnapshot: publishCaretSnapshot,
    clearSelectionSnapshot,
  } = caretController;

  React.useEffect(() => {
    // Only resync DOM when the rendered block actually changes to avoid caret jumps.
    if (blockVersionRef.current === blockId) {
      return;
    }
    blockVersionRef.current = blockId;
    clearDebounce();
    textRef.current = initialValue;
    lastSyncedRef.current = initialValue;
    setTextContent(initialValue);
  }, [blockId, clearDebounce, initialValue, setTextContent]);

  const hasText = React.useCallback(() => !isTextEffectivelyEmpty(textRef.current), []);

  React.useImperativeHandle(ref, () => ({
    getText: () => textRef.current,
    hasText,
    isCaretAtEdge,
    focusAtEdge: placeCaretAtEdge,
    setCaretOffset: placeCaretAtOffset,
    setText: setTextContent,
    getCaretRect,
    getCaretOffset,
    focusFromPoint,
    getOffsetFromPoint,
  }), [focusFromPoint, getCaretOffset, getCaretRect, getOffsetFromPoint, hasText, isCaretAtEdge, placeCaretAtEdge, placeCaretAtOffset, setTextContent]);

  React.useEffect(() => {
    registerBlockEditorHandle(blockId, () => ({
      getText: () => textRef.current,
      hasText,
      isCaretAtEdge,
      focusAtEdge: placeCaretAtEdge,
      setCaretOffset: placeCaretAtOffset,
      setText: setTextContent,
      getCaretRect,
      getCaretOffset,
      focusFromPoint,
      getOffsetFromPoint,
    }));
    return () => unregisterBlockEditorHandle(blockId);
  }, [blockId, focusFromPoint, getCaretOffset, getCaretRect, getOffsetFromPoint, hasText, isCaretAtEdge, placeCaretAtEdge, placeCaretAtOffset]);

  const handleInput = (event: React.FormEvent<HTMLDivElement>) => {
    const nextValue = extractInlineTextFromEditable(event.currentTarget);
    textRef.current = nextValue;
    updateEmptyState(nextValue);
    onImmediateChange?.(nextValue);
    scheduleDebounce();
    publishCaretSnapshot(undefined, nextValue.length);
  };

  const handleKeyDownInternal = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (readOnly && (event.key === 'Enter' || event.key === ' ' || event.key.length === 1)) {
      event.preventDefault();
      announceFocusIntent('keyboard', blockId, { ttlMs: 600, source: 'block-editor-core.readonly-keydown' });
      onRequestStartEdit?.({ source: 'key', key: event.key, shiftKey: event.shiftKey });
      return;
    }
    onKeyDown?.(event);
  };

  const handleClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (readOnly) {
      event.stopPropagation();
      onRequestStartEdit?.({ source: 'click' });
      return;
    }
    onClick?.(event);
  };

  const handleFocus = (event: React.FocusEvent<HTMLDivElement>) => {
    if (readOnly) {
      onRequestStartEdit?.({ source: 'focus' });
      return;
    }
    onFocus?.(event);
  };

  const handleBlur = (event: React.FocusEvent<HTMLDivElement>) => {
    flushSync();
    clearSelectionSnapshot();
    onBlur?.(event);
  };

  const handleMouseDownCapture = React.useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const offset = getOffsetFromPoint(event.clientX, event.clientY);
    announceFocusIntent('pointer', blockId, {
      ttlMs: 600,
      payload: typeof offset === 'number' ? { offset } : undefined,
      source: 'block-editor-core.pointer-capture',
    });
  }, [blockId, getOffsetFromPoint]);

  return (
    <div className={styles.textBlockShell}>
      <div
        ref={editableRef}
        className={[styles.textBlockContent, className].filter(Boolean).join(' ')}
        role="textbox"
        contentEditable={!readOnly}
        suppressContentEditableWarning
        tabIndex={readOnly ? 0 : undefined}
        data-placeholder={placeholder}
        data-empty={isEmpty ? 'true' : undefined}
        onInput={handleInput}
        onKeyDown={handleKeyDownInternal}
        onMouseDownCapture={handleMouseDownCapture}
        onClick={handleClick}
        onFocus={handleFocus}
        onBlur={handleBlur}
        {...rest}
      />
    </div>
  );
});

BlockEditorCore.displayName = 'BlockEditorCore';
