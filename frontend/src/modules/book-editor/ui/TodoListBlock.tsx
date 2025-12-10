'use client';

import React from 'react';
import type { TodoListBlockContent, TodoListItemContent } from '@/entities/block';
import { generateBlockScopedId } from '@/entities/block';
import { ParagraphEditor } from './ParagraphEditor';
import styles from './bookEditor.module.css';
import { announceFocusIntent, clearFocusIntent, focusIntentStore, type FocusIntentKind } from '../model/selectionStore';
import { getBlockEditorHandle } from '../model/editorRegistry';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';
import type { KeyboardAction, KeyboardContextInput, KeyboardIntent } from '../model/keyboardDecider';
import { useI18n } from '@/i18n/useI18n';

const useTodoCopy = () => {
  const { t } = useI18n();
  return React.useMemo(
    () => ({
      placeholder: t('books.blocks.editor.todo.placeholder'),
      emptyList: t('books.blocks.editor.todo.empty'),
      ariaLabel: t('books.blocks.editor.todo.aria'),
      promotedBadge: t('books.blocks.editor.todo.badge.promoted'),
    }),
    [t],
  );
};
const isItemEmpty = (item: TodoListItemContent) => !item.text || item.text.trim().length === 0;
const areAllItemsEmpty = (items: TodoListItemContent[]) => items.every((item) => isItemEmpty(item));

interface TodoListDisplayProps {
  content: TodoListBlockContent;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const TodoListDisplay: React.FC<TodoListDisplayProps> = ({ content, onStartEdit }) => {
  const items = Array.isArray(content?.items) ? content.items : [];
  const { placeholder, emptyList, ariaLabel, promotedBadge } = useTodoCopy();
  return (
    <div
      className={styles.todoList}
      role="group"
      aria-label={ariaLabel}
      tabIndex={0}
      onClick={(event) => {
        event.stopPropagation();
        onStartEdit({ source: 'click' });
      }}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          onStartEdit({ source: 'key', key: event.key, shiftKey: event.shiftKey });
        }
      }}
    >
      {items.length === 0 ? (
        <p className={styles.placeholder}>{emptyList}</p>
      ) : (
        items.map((item) => {
          const rawText = typeof item.text === 'string' ? item.text : '';
          const isEmpty = rawText.trim().length === 0;
          const displayText = isEmpty ? placeholder : rawText;
          return (
            <div key={item.id} className={`${styles.inlineRow} ${styles.todoRow} ${styles.todoListItem}`}>
              <input type="checkbox" className={styles.todoCheckbox} checked={Boolean(item.checked)} readOnly />
              <span
                className={`${styles.todoText} ${item.checked ? styles.todoTextChecked : ''} ${isEmpty ? styles.placeholder : ''}`}
              >
                {displayText}
              </span>
              {item.isPromoted && <span className={styles.todoBadge}>{promotedBadge}</span>}
            </div>
          );
        })
      )}
    </div>
  );
};

interface TodoListEditorProps {
  blockId: string;
  content: TodoListBlockContent;
  onChange: (next: TodoListBlockContent) => void;
  onExitEdit: () => void;
  onDeleteEmptyBlock?: () => void;
  onSoftBreak?: () => void;
  autoFocus?: boolean;
  readOnly?: boolean;
  onStartEdit?: (request?: BlockEditorStartEditRequest) => void;
  onFocusPrev?: () => void;
  onFocusNext?: () => void;
  onCreateSiblingBlock?: () => void;
}

export const TodoListEditor: React.FC<TodoListEditorProps> = ({
  blockId,
  content,
  onChange,
  onExitEdit,
  onDeleteEmptyBlock,
  onSoftBreak,
  autoFocus,
  readOnly,
  onStartEdit,
  onFocusPrev,
  onFocusNext,
  onCreateSiblingBlock,
}) => {
  const items = React.useMemo(() => (Array.isArray(content?.items) ? content.items : []), [content]);
  const itemCount = items.length;
  const allItemsEmpty = React.useMemo(() => areAllItemsEmpty(items), [items]);
  const pendingAllEmptyExitRef = React.useRef(false);
  React.useEffect(() => {
    if (!allItemsEmpty && pendingAllEmptyExitRef.current) {
      pendingAllEmptyExitRef.current = false;
    }
  }, [allItemsEmpty]);
  const clearPendingAllEmptyExit = React.useCallback(() => {
    if (pendingAllEmptyExitRef.current) {
      pendingAllEmptyExitRef.current = false;
    }
  }, []);
  const commitItems = React.useCallback(
    (nextItems: TodoListItemContent[]) => {
      onChange({ ...content, items: nextItems });
    },
    [content, onChange],
  );
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[TodoListEditor items]', {
        blockId,
        length: items.length,
        ids: items.map((item) => item.id),
        emptyFlags: items.map((item) => !item.text || !item.text.trim()),
      });
    }
  }, [blockId, items]);
  const rootRef = React.useRef<HTMLDivElement | null>(null);
  const [pendingFocusId, setPendingFocusId] = React.useState<string | null>(null);
  const autoFocusAppliedRef = React.useRef(false);
  const buildRowId = React.useCallback((focusKey: string) => `${blockId}-${focusKey}`, [blockId]);
  const rowIdPrefix = React.useMemo(() => `${blockId}-`, [blockId]);
  const resolveFirstFocusKey = React.useCallback(() => items[0]?.id ?? (items.length ? `todo-fallback-0` : null), [items]);

  const queueRowFocus = React.useCallback(
    (focusKey: string | null, source: FocusIntentKind = 'keyboard') => {
      if (!focusKey || source === 'pointer') {
        return;
      }
      setPendingFocusId(focusKey);
      announceFocusIntent(source, buildRowId(focusKey), {
        source: `todo-editor.queue-focus.${source}`,
      });
    },
    [buildRowId],
  );

  React.useEffect(() => {
    if (!items.some((item) => !item.id)) {
      return;
    }
    const patched = items.map((item) => (item.id ? item : { ...item, id: generateBlockScopedId() }));
    onChange({ ...content, items: patched });
  }, [items, content, onChange]);

  React.useEffect(() => {
    if (readOnly) {
      autoFocusAppliedRef.current = false;
      return;
    }
    if (!autoFocus || autoFocusAppliedRef.current) {
      return;
    }
    autoFocusAppliedRef.current = true;
    const intent = focusIntentStore.getIntent();
    if (intent?.kind === 'pointer') {
      if (!intent.targetId || intent.targetId === blockId || intent.targetId.startsWith(rowIdPrefix)) {
        setPendingFocusId(null);
        return;
      }
    }
    const firstId = resolveFirstFocusKey();
    if (!firstId) {
      return;
    }
    if (intent && intent.kind !== 'pointer') {
      if (intent.targetId && intent.targetId.startsWith(rowIdPrefix)) {
        return;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return;
      }
      clearFocusIntent(intent.token);
      queueRowFocus(firstId, intent.kind);
      return;
    }
    queueRowFocus(firstId, 'initial');
  }, [autoFocus, blockId, queueRowFocus, readOnly, resolveFirstFocusKey, rowIdPrefix]);

  React.useEffect(() => {
    if (readOnly) {
      return;
    }
    const unsubscribe = focusIntentStore.subscribe(() => {
      const intent = focusIntentStore.getIntent();
      if (!intent || intent.kind === 'pointer') {
        return;
      }
      if (intent.targetId && intent.targetId.startsWith(rowIdPrefix)) {
        return;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return;
      }
      const firstId = resolveFirstFocusKey();
      if (!firstId) {
        return;
      }
      clearFocusIntent(intent.token);
      queueRowFocus(firstId, intent.kind);
    });
    return () => unsubscribe();
  }, [blockId, queueRowFocus, readOnly, resolveFirstFocusKey, rowIdPrefix]);

  React.useEffect(() => {
    if (readOnly) {
      return;
    }
    const unsubscribe = focusIntentStore.subscribe(() => {
      const intent = focusIntentStore.getIntent();
      if (!intent || intent.kind !== 'pointer') {
        return;
      }
      if (!intent.targetId) {
        return;
      }
      if (intent.targetId === blockId || intent.targetId.startsWith(rowIdPrefix)) {
        setPendingFocusId(null);
      }
    });
    return () => unsubscribe();
  }, [blockId, readOnly, rowIdPrefix]);

  React.useEffect(() => {
    if (!pendingFocusId || readOnly) {
      return;
    }
    const frame = requestAnimationFrame(() => setPendingFocusId(null));
    return () => cancelAnimationFrame(frame);
  }, [pendingFocusId, readOnly]);

  const ensureEditingMode = React.useCallback(
    (focusId?: string, options?: { source?: FocusIntentKind }) => {
      if (focusId && options?.source !== 'pointer') {
        queueRowFocus(focusId, options?.source);
      }
      if (readOnly) {
        onStartEdit?.();
      }
    },
    [onStartEdit, queueRowFocus, readOnly],
  );

  const updateItem = React.useCallback(
    (target: TodoListItemContent, patch: Partial<TodoListItemContent>) => {
      const nextItems = items.map((item) => (item.id === target.id ? { ...item, ...patch } : item));
      commitItems(nextItems);
      if (typeof patch.text === 'string' && patch.text.trim().length > 0) {
        clearPendingAllEmptyExit();
      }
    },
    [clearPendingAllEmptyExit, commitItems, items],
  );

  const ensureAtLeastOneItem = React.useCallback(() => {
    const fallback: TodoListItemContent = { id: generateBlockScopedId(), text: '', checked: false };
    commitItems([fallback]);
    queueRowFocus(fallback.id ?? 'todo-fallback-0');
  }, [commitItems, queueRowFocus]);

  const removeItem = React.useCallback(
    (target: TodoListItemContent) => {
      clearPendingAllEmptyExit();
      const index = items.findIndex((item) => item.id === target.id);
      const nextItems = items.filter((item) => item.id !== target.id);
      if (nextItems.length === 0) {
        ensureAtLeastOneItem();
        return;
      }
      commitItems(nextItems);
      const fallbackIndex = Math.max(0, Math.min(index, nextItems.length - 1));
      const fallback = nextItems[fallbackIndex];
      if (fallback?.id) {
        queueRowFocus(fallback.id);
      }
    },
    [clearPendingAllEmptyExit, commitItems, ensureAtLeastOneItem, items, queueRowFocus],
  );

  const insertItemAfter = React.useCallback(
    (target: TodoListItemContent, options?: { skipPendingReset?: boolean }) => {
      if (!options?.skipPendingReset) {
        clearPendingAllEmptyExit();
      }
      const index = items.findIndex((item) => item.id === target.id);
      const nextItem: TodoListItemContent = { id: generateBlockScopedId(), text: '', checked: false };
      const nextItems = [...items];
      const insertPosition = index === -1 ? nextItems.length : index + 1;
      nextItems.splice(insertPosition, 0, nextItem);
      commitItems(nextItems);
      queueRowFocus(nextItem.id ?? `todo-fallback-${insertPosition}`);
    },
    [clearPendingAllEmptyExit, commitItems, items, queueRowFocus],
  );

  const focusSibling = React.useCallback(
    (target: TodoListItemContent, direction: 'prev' | 'next'): boolean => {
      const index = items.findIndex((item) => item.id === target.id);
      const nextIndex = direction === 'prev' ? index - 1 : index + 1;
      if (nextIndex >= 0 && nextIndex < items.length) {
        const focusKey = items[nextIndex]?.id ?? `todo-fallback-${nextIndex}`;
        queueRowFocus(focusKey);
        return true;
      }
      return false;
    },
    [items, queueRowFocus],
  );

  const exitEmptyTodoBlock = React.useCallback(() => {
    clearPendingAllEmptyExit();
    onExitEdit();
    onDeleteEmptyBlock?.();
  }, [clearPendingAllEmptyExit, onDeleteEmptyBlock, onExitEdit]);

  const exitTodoAndCreateSibling = React.useCallback(
    (target: TodoListItemContent) => {
      clearPendingAllEmptyExit();
      if (items.length <= 1) {
        exitEmptyTodoBlock();
        return;
      }
      const nextItems = items.filter((item) => item.id !== target.id);
      commitItems(nextItems);
      onExitEdit();
      onCreateSiblingBlock?.();
    },
    [clearPendingAllEmptyExit, commitItems, exitEmptyTodoBlock, items, onCreateSiblingBlock, onExitEdit],
  );

  const buildKeyboardContext = React.useCallback(
    (target: TodoListItemContent, index: number): KeyboardContextInput => ({
      kind: 'todo-item',
      isFirstItem: index === 0,
      isLastItem: index === itemCount - 1,
      allItemsEmpty,
      isItemEmpty: isItemEmpty(target),
    }),
    [allItemsEmpty, itemCount],
  );

  const handleKeyboardDecision = React.useCallback(
    (target: TodoListItemContent, payload: { intent: KeyboardIntent; decision: KeyboardAction }) => {
      if (payload.decision === 'todo-insert-item') {
        insertItemAfter(target);
        return true;
      }
      if (payload.decision === 'todo-remove-item') {
        removeItem(target);
        return true;
      }
      if (payload.decision === 'todo-exit') {
        if (payload.intent === 'enter' && allItemsEmpty && !pendingAllEmptyExitRef.current) {
          insertItemAfter(target, { skipPendingReset: true });
          pendingAllEmptyExitRef.current = true;
          return true;
        }
        pendingAllEmptyExitRef.current = false;
        if (allItemsEmpty) {
          exitEmptyTodoBlock();
          return true;
        }
        exitTodoAndCreateSibling(target);
        return true;
      }
      return false;
    },
    [allItemsEmpty, exitEmptyTodoBlock, exitTodoAndCreateSibling, insertItemAfter, removeItem],
  );

  const handleBlurCapture = (event: React.FocusEvent<HTMLDivElement>) => {
    const next = event.relatedTarget as Node | null;
    if (next && rootRef.current?.contains(next)) {
      return;
    }
    onExitEdit();
  };

  return (
    <div
      ref={rootRef}
      className={styles.todoList}
      onBlurCapture={handleBlurCapture}
    >
      {items.map((item, index) => {
        const focusKey = item.id ?? `todo-fallback-${index}`;
        const rowEditorId = `${blockId}-${focusKey}`;
        return (
          <TodoRow
            key={focusKey}
            rowEditorId={rowEditorId}
            item={item}
            readOnly={readOnly}
            autoFocus={!readOnly && pendingFocusId === focusKey}
            onToggleChecked={(checked) => {
              ensureEditingMode();
              updateItem(item, { checked });
            }}
            onChangeText={(text) => updateItem(item, { text })}
            onSubmitNew={() => insertItemAfter(item)}
            onDeleteEmpty={() => removeItem(item)}
            onFocusPrev={() => {
              if (!focusSibling(item, 'prev')) {
                onFocusPrev?.();
              }
            }}
            onFocusNext={() => {
              if (!focusSibling(item, 'next')) {
                onFocusNext?.();
              }
            }}
            onRequestEdit={() => ensureEditingMode(focusKey)}
            onPointerRequestEdit={() => ensureEditingMode(focusKey, { source: 'pointer' })}
            onExitEdit={onExitEdit}
            onSoftBreak={() => onSoftBreak?.()}
            getKeyboardContext={() => buildKeyboardContext(item, index)}
            onKeyboardDecision={(payload) => handleKeyboardDecision(item, payload)}
          />
        );
      })}
    </div>
  );
};

interface TodoRowProps {
  rowEditorId: string;
  item: TodoListItemContent;
  readOnly?: boolean;
  autoFocus: boolean;
  onRequestEdit: () => void;
  onPointerRequestEdit?: () => void;
  onToggleChecked: (checked: boolean) => void;
  onChangeText: (text: string) => void;
  onSubmitNew: () => void;
  onDeleteEmpty: () => void;
  onFocusPrev: () => void;
  onFocusNext: () => void;
  onExitEdit: () => void;
  onSoftBreak?: () => void;
  getKeyboardContext?: (intent: KeyboardIntent) => KeyboardContextInput | null;
  onKeyboardDecision?: (payload: { intent: KeyboardIntent; decision: KeyboardAction }) => boolean | void;
}

const TodoRow: React.FC<TodoRowProps> = ({
  rowEditorId,
  item,
  readOnly,
  autoFocus,
  onRequestEdit,
  onPointerRequestEdit,
  onToggleChecked,
  onChangeText,
  onSubmitNew,
  onDeleteEmpty,
  onFocusPrev,
  onFocusNext,
  onExitEdit,
  onSoftBreak,
  getKeyboardContext,
  onKeyboardDecision,
}) => {
  const { placeholder, promotedBadge } = useTodoCopy();
  const handlePointerCapture = (event: React.MouseEvent<HTMLDivElement>) => {
    if (event.button !== 0) {
      return;
    }
    const target = event.target as HTMLElement | null;
    if (target?.closest('[contenteditable="true"]')) {
      return;
    }
    if (target?.closest('input[type="checkbox"]')) {
      return;
    }
    const editorHandle = getBlockEditorHandle(rowEditorId);
    if (!editorHandle) {
      return;
    }
    event.preventDefault();
    event.stopPropagation();
    const pointerOffset = editorHandle.getOffsetFromPoint?.(event.clientX, event.clientY);
    announceFocusIntent('pointer', rowEditorId, {
      ttlMs: 600,
      payload: typeof pointerOffset === 'number' ? { offset: pointerOffset } : undefined,
      source: 'todo-editor.pointer-capture',
    });
    const focusFromPointer = () => {
      requestAnimationFrame(() => {
        editorHandle.focusFromPoint?.(event.clientX, event.clientY);
      });
    };
    if (readOnly) {
      (onPointerRequestEdit ?? onRequestEdit)();
      requestAnimationFrame(() => {
        requestAnimationFrame(focusFromPointer);
      });
      return;
    }
    focusFromPointer();
  };

  return (
    <div
      className={`${styles.inlineRow} ${styles.todoRow} ${styles.todoEditorRow}`}
      onMouseDownCapture={handlePointerCapture}
    >
      <input
        type="checkbox"
        className={styles.todoCheckbox}
        checked={Boolean(item.checked)}
        onChange={(event) => onToggleChecked(event.target.checked)}
      />
      <div className={styles.inlineEditorText}>
        <ParagraphEditor
          blockId={rowEditorId}
          value={item.text ?? ''}
          placeholder={placeholder}
          readOnly={readOnly}
          autoFocus={autoFocus}
          onChange={onChangeText}
          onSubmit={onSubmitNew}
          onExitEdit={onExitEdit}
          onSoftBreak={onSoftBreak}
          onDeleteEmptyBlock={onDeleteEmpty}
          onStartEdit={onRequestEdit}
          onFocusPrev={onFocusPrev}
          onFocusNext={onFocusNext}
          suppressBlurExit
          getKeyboardContext={getKeyboardContext}
          onKeyboardDecision={onKeyboardDecision}
        />
      </div>
      {item.isPromoted && <span className={styles.todoBadge}>{promotedBadge}</span>}
    </div>
  );
};

