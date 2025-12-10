'use client';

import React from 'react';
import styles from './bookEditor.module.css';
import { handleInlineEditorKeyDown } from '../model/keyboard';
import type { BlockKind } from '@/entities/block';
import { detectMarkdownShortcut, isCaretInEmptySegment } from '../model/markdownShortcuts';
import { BlockEditorCore, type BlockEditorCoreHandle, type BlockEditorStartEditRequest } from './BlockEditorCore';
import {
  decideKeyboardAction,
  type KeyboardAction,
  type KeyboardContext,
  type KeyboardContextInput,
  type KeyboardIntent,
} from '../model/keyboardDecider';
import { insertSoftBreakAt } from '../model/inlineText';
import { useI18n } from '@/i18n/useI18n';

export type ParagraphEditorVariant = 'paragraph' | 'heading-1' | 'heading-2' | 'heading-3';

export interface MarkdownShortcutRequest {
  kind: BlockKind;
  cleared?: boolean;
}

export interface ParagraphEditorProps {
  blockId: string;
  value: string;
  variant?: ParagraphEditorVariant;
  autoFocus?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onExitEdit: () => void;
  onSoftBreak?: () => void;
  onDeleteEmptyBlock?: () => void;
  readOnly?: boolean;
  onStartEdit?: (request?: BlockEditorStartEditRequest) => void;
  placeholder?: string;
  onFocusPrev?: () => void;
  onFocusNext?: () => void;
  focusPosition?: 'start' | 'end';
  onRequestSlashMenu?: () => void;
  suppressBlurExit?: boolean;
  onMarkdownShortcut?: (request: MarkdownShortcutRequest) => void;
  getKeyboardContext?: (intent: KeyboardIntent) => KeyboardContextInput | null;
  onKeyboardDecision?: (payload: { intent: KeyboardIntent; decision: KeyboardAction }) => boolean | void;
}

export const ParagraphEditor: React.FC<ParagraphEditorProps> = ({
  blockId,
  value,
  variant = 'paragraph',
  autoFocus,
  onChange,
  onSubmit,
  onExitEdit,
  onSoftBreak,
  onDeleteEmptyBlock,
  readOnly,
  onStartEdit,
  placeholder,
  onFocusPrev,
  onFocusNext,
  focusPosition,
  onRequestSlashMenu,
  suppressBlurExit,
  onMarkdownShortcut,
  getKeyboardContext,
  onKeyboardDecision,
}) => {
  const coreRef = React.useRef<BlockEditorCoreHandle | null>(null);
  const { t } = useI18n();
  const derivedPlaceholder = placeholder
    ?? (variant?.startsWith('heading')
      ? t('books.blocks.editor.paragraph.headingPlaceholder')
      : t('books.blocks.editor.paragraph.placeholder'));
  const variantClass = variant ? styles[variant] : undefined;
  const editorClassName = [variantClass, readOnly ? styles.readonlyShell : undefined].filter(Boolean).join(' ');

  const hasText = React.useCallback(() => {
    if (coreRef.current) {
      return coreRef.current.hasText();
    }
    return Boolean(value?.trim());
  }, [value]);

  const readCurrentText = React.useCallback(() => {
    if (coreRef.current) {
      return coreRef.current.getText() ?? '';
    }
    return value ?? '';
  }, [value]);

  const isCaretAtEdge = React.useCallback((edge: 'start' | 'end') => {
    return coreRef.current?.isCaretAtEdge(edge) ?? false;
  }, []);

  const isCaretInEmptySegmentLocal = React.useCallback(() => {
    const handle = coreRef.current;
    if (!handle) {
      return !hasText();
    }
    const caretOffset = handle.getCaretOffset();
    if (caretOffset == null) {
      return !hasText();
    }
    const textContent = handle.getText() ?? '';
    return isCaretInEmptySegment(textContent, caretOffset);
  }, [hasText]);

  const detectMarkdownShortcutLocal = React.useCallback((): BlockKind | null => {
    const handle = coreRef.current;
    if (!handle) {
      return null;
    }
    const caretOffset = handle.getCaretOffset();
    if (caretOffset == null) {
      return null;
    }
    return detectMarkdownShortcut(handle.getText() ?? '', caretOffset);
  }, []);

  const resolveKeyboardContext = React.useCallback(
    (intent: KeyboardIntent): KeyboardContext | null => {
      if (!getKeyboardContext) {
        return null;
      }
      const base = getKeyboardContext(intent);
      if (!base) {
        return null;
      }
      const hasInline = hasText();
      if ('kind' in base && base.kind === 'list-item') {
        return {
          ...base,
          isItemEmpty: base.isItemEmpty ?? !hasInline,
        };
      }
      if ('kind' in base && base.kind === 'todo-item') {
        return {
          ...base,
          isItemEmpty: base.isItemEmpty ?? !hasInline,
        };
      }
      return {
        kind: 'block',
        blockKind: base.blockKind,
        isBlockEmpty: base.isBlockEmpty,
        hasInlineText: hasInline,
        caretAtStart: isCaretAtEdge('start'),
        caretAtEnd: isCaretAtEdge('end'),
        preferExitForLonelyEmpty: base.preferExitForLonelyEmpty,
      };
    },
    [getKeyboardContext, hasText, isCaretAtEdge],
  );

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    const isComposing = Boolean((event.nativeEvent as { isComposing?: boolean })?.isComposing);
    if ((event.key === 'Enter' || event.key === ' ') && process.env.NODE_ENV !== 'production') {
      const currentText = readCurrentText();
      console.log('[PE key]', {
        key: event.key,
        blockId,
        variant,
        hasText: hasText(),
        caretStart: isCaretAtEdge('start'),
        caretEnd: isCaretAtEdge('end'),
        caretOffset: coreRef.current?.getCaretOffset() ?? null,
        textPreview: currentText.length > 40 ? `${currentText.slice(0, 40)}…` : currentText,
      });
    }

    if (event.isDefaultPrevented()) {
      return;
    }

    if (event.key === 'Enter' && event.shiftKey) {
      if (isComposing) {
        return;
      }
      event.preventDefault();
      const handle = coreRef.current;
      const currentText = handle?.getText() ?? value ?? '';
      const caretOffset = handle?.getCaretOffset();
      const { text: nextText, caretOffset: nextCaretOffset } = insertSoftBreakAt(currentText, caretOffset);
      if (handle) {
        handle.setText(nextText);
        handle.setCaretOffset(nextCaretOffset);
      }
      onChange(nextText);
      onSoftBreak?.();
      return;
    }

    const tryHandleKeyboardIntent = (intent: KeyboardIntent): boolean => {
      const context = resolveKeyboardContext(intent);
      if (!context) {
        return false;
      }
      const decision = decideKeyboardAction(intent, context);
      if (process.env.NODE_ENV !== 'production') {
        console.log('[PE keyboardDecision]', {
          blockId,
          intent,
          decision,
          context,
        });
      }

      if (context.kind !== 'block') {
        const handledByParent = onKeyboardDecision?.({ intent, decision });
        if (handledByParent) {
          event.preventDefault();
          return true;
        }
        return false;
      }

      if (decision === 'noop') {
        return false;
      }

      event.preventDefault();
      if (decision === 'exit-edit') {
        onExitEdit();
        return true;
      }
      if (decision === 'split' || decision === 'create-below') {
        onSubmit();
        return true;
      }
      if (decision === 'delete-block') {
        onDeleteEmptyBlock?.();
        return true;
      }
      return true;
    };

    if (event.key === 'Enter' && !event.shiftKey) {
      if (tryHandleKeyboardIntent('enter')) {
        return;
      }
    }

    if (event.key === 'Backspace' && !event.shiftKey) {
      if (tryHandleKeyboardIntent('backspace')) {
        return;
      }
    }

    if (event.key === 'ArrowUp' && !event.shiftKey && isCaretAtEdge('start')) {
      event.preventDefault();
      onFocusPrev?.();
      return;
    }

    if (event.key === 'ArrowDown' && !event.shiftKey && isCaretAtEdge('end')) {
      event.preventDefault();
      onFocusNext?.();
      return;
    }

    if (event.key === 'Backspace' && !event.shiftKey && !hasText() && isCaretAtEdge('start')) {
      event.preventDefault();
      onDeleteEmptyBlock?.();
      return;
    }

    if (isComposing) {
      return;
    }

    if (event.key === '/' && !event.shiftKey && isCaretInEmptySegmentLocal()) {
      event.preventDefault();
      onRequestSlashMenu?.();
      return;
    }

    if (event.key === ' ' && !event.shiftKey && onMarkdownShortcut) {
      const shortcutKind = detectMarkdownShortcutLocal();
      if (process.env.NODE_ENV !== 'production') {
        const snapshot = readCurrentText();
        console.log('[PE shortcutCheck]', {
          blockId,
          textPreview: snapshot.length > 40 ? `${snapshot.slice(0, 40)}…` : snapshot,
          caretOffset: coreRef.current?.getCaretOffset() ?? null,
          shortcutKind,
        });
      }
      if (shortcutKind) {
        event.preventDefault();
        coreRef.current?.setText('');
        onChange('');
        onMarkdownShortcut({ kind: shortcutKind, cleared: true });
        return;
      }
    }

    handleInlineEditorKeyDown(event, {
      hasText,
      onSubmit,
      onSoftBreak: () => onSoftBreak?.(),
      onExitEdit,
      onDeleteEmptyBlock: () => onDeleteEmptyBlock?.(),
    });
  };

  return (
    <BlockEditorCore
      ref={(instance) => {
        coreRef.current = instance;
      }}
      blockId={blockId}
      initialValue={value}
      autoFocus={autoFocus}
      focusPosition={focusPosition}
      readOnly={readOnly}
      placeholder={derivedPlaceholder}
      data-readonly={readOnly ? 'true' : undefined}
      className={editorClassName}
      onImmediateChange={(next) => onChange(next)}
      onRequestStartEdit={onStartEdit}
      onKeyDown={handleKeyDown}
      onBlur={() => {
        if (!readOnly && !suppressBlurExit) {
          onExitEdit();
        }
      }}
    />
  );
};
