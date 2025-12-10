'use client';

import React from 'react';
import type { ListBlockContent } from '@/entities/block';
import { ParagraphEditor } from './ParagraphEditor';
import styles from './bookEditor.module.css';
import { announceFocusIntent, clearFocusIntent, focusIntentStore, type FocusIntentKind } from '../model/selectionStore';
import { getBlockEditorHandle } from '../model/editorRegistry';
import type { BlockEditorStartEditRequest } from './BlockEditorCore';
import type { KeyboardAction, KeyboardContextInput, KeyboardIntent } from '../model/keyboardDecider';
import { useI18n } from '@/i18n/useI18n';

interface ListItemModel {
  id: string;
  text: string;
}

const ZERO_WIDTH_REGEX = /[\u200B-\u200D\uFEFF]/g;
const normalizeForEmptyCheck = (value?: string) => (value ?? '').replace(ZERO_WIDTH_REGEX, '').trim();

const normalizeItems = (blockId: string, items?: ListBlockContent['items']): ListItemModel[] => {
  if (!Array.isArray(items) || items.length === 0) {
    return [{ id: `${blockId}-item-0`, text: '' }];
  }
  return items.map((item, index) => {
    if (typeof item === 'string') {
      return { id: `${blockId}-item-${index}`, text: item };
    }
    if (!item || typeof item !== 'object') {
      return { id: `${blockId}-item-${index}`, text: String(item ?? '') };
    }
    if ('text' in item && typeof (item as any).text === 'string') {
      return { id: `${blockId}-item-${index}`, text: (item as any).text };
    }
    return { id: `${blockId}-item-${index}`, text: String((item as any).text ?? '') };
  });
};

interface ListDisplayProps {
  content: ListBlockContent;
  ordered?: boolean;
  onStartEdit: (request?: BlockEditorStartEditRequest) => void;
}

export const ListDisplay: React.FC<ListDisplayProps> = ({ content, ordered, onStartEdit }) => {
  const items = normalizeItems('display', content?.items);
  const hasItems = items.some((item) => Boolean(normalizeForEmptyCheck(item.text)));
  const { t } = useI18n();
  const placeholder = t('books.blocks.editor.list.placeholder');
  const emptyCopy = t('books.blocks.editor.list.empty');
  const ariaOrdered = t('books.blocks.editor.list.aria.ordered');
  const ariaUnordered = t('books.blocks.editor.list.aria.unordered');
  return (
    <div
      className={`${styles.todoList} ${styles.listBlock}`}
      role="group"
      aria-label={ordered ? ariaOrdered : ariaUnordered}
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
      {!hasItems ? (
        <p className={styles.placeholder}>{emptyCopy}</p>
      ) : (
        items.map((item, index) => {
          const trimmed = normalizeForEmptyCheck(item.text);
          const text = trimmed ? trimmed : placeholder;
          const placeholder = !trimmed;
          return (
            <div key={`list-display-${index}`} className={`${styles.inlineRow}`}>
              <span
                className={`${styles.inlineMarker} ${ordered ? styles.inlineMarkerOrdered : styles.inlineMarkerBullet}`}
              >
                {ordered ? index + 1 : '•'}
              </span>
              <span className={`${styles.todoText} ${placeholder ? styles.placeholder : ''}`}>{text}</span>
            </div>
          );
        })
      )}
    </div>
  );
};

interface ListEditorProps {
  blockId: string;
  content: ListBlockContent;
  ordered?: boolean;
  onChange: (next: ListBlockContent) => void;
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

export const ListEditor: React.FC<ListEditorProps> = ({
  blockId,
  content,
  ordered,
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
  const { t } = useI18n();
  const itemPlaceholder = React.useMemo(() => t('books.blocks.editor.list.placeholder'), [t]);
  const items = React.useMemo(() => normalizeItems(blockId, content?.items), [blockId, content]);
  const pendingAllEmptyExitRef = React.useRef(false);
  React.useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      console.log('[ListEditor items]', {
        blockId,
        ordered,
        length: items.length,
        texts: items.map((item) => item.text),
      });
    }
  }, [blockId, items, ordered]);
  const rootRef = React.useRef<HTMLDivElement | null>(null);
  const [pendingFocusIndex, setPendingFocusIndex] = React.useState<number | null>(null);
  const autoFocusAppliedRef = React.useRef(false);
  const buildRowId = React.useCallback((index: number) => `${blockId}-item-${index}`, [blockId]);
  const rowIdPrefix = React.useMemo(() => `${blockId}-item-`, [blockId]);

  const queueRowFocus = React.useCallback(
    (index: number, source: FocusIntentKind = 'keyboard') => {
      if (typeof index !== 'number' || index < 0) {
        return;
      }
      setPendingFocusIndex(index);
      announceFocusIntent(source, buildRowId(index), {
        source: `list-editor.queue-focus.${source}`,
      });
    },
    [buildRowId],
  );

  const listKind: 'bulleted_list' | 'numbered_list' = ordered ? 'numbered_list' : 'bulleted_list';
  const normalizedTexts = React.useMemo(() => items.map((item) => normalizeForEmptyCheck(item.text)), [items]);
  const allItemsEmpty = React.useMemo(() => normalizedTexts.every((text) => !text), [normalizedTexts]);
  const itemCount = items.length;

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

  const buildKeyboardContext = React.useCallback(
    (index: number): KeyboardContextInput => ({
      kind: 'list-item',
      listKind,
      isFirstItem: index === 0,
      isLastItem: index === itemCount - 1,
      allItemsEmpty,
    }),
    [allItemsEmpty, itemCount, listKind],
  );

  const commitItems = React.useCallback(
    (nextItems: ListItemModel[]) => {
      const ensured = nextItems.length ? nextItems : [{ id: `${blockId}-item-0`, text: '' }];
      onChange({ ...content, items: ensured.map((item) => item.text) });
    },
    [blockId, content, onChange],
  );

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
        setPendingFocusIndex(null);
        return;
      }
    }
    if (intent && intent.kind !== 'pointer') {
      if (intent.targetId && intent.targetId.startsWith(rowIdPrefix)) {
        return;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return;
      }
      clearFocusIntent(intent.token);
      queueRowFocus(0, intent.kind);
      return;
    }
    queueRowFocus(0, 'initial');
  }, [autoFocus, blockId, queueRowFocus, readOnly, rowIdPrefix]);

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
      clearFocusIntent(intent.token);
      queueRowFocus(0, intent.kind);
    });
    return () => unsubscribe();
  }, [blockId, queueRowFocus, readOnly, rowIdPrefix]);

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
        setPendingFocusIndex(null);
      }
    });
    return () => unsubscribe();
  }, [blockId, readOnly, rowIdPrefix]);

  React.useEffect(() => {
    if (pendingFocusIndex == null || readOnly) {
      return;
    }
    const frame = requestAnimationFrame(() => setPendingFocusIndex(null));
    return () => cancelAnimationFrame(frame);
  }, [pendingFocusIndex, readOnly]);

  const ensureEditingMode = React.useCallback(
    (focusIndex?: number, options?: { source?: FocusIntentKind }) => {
      if (typeof focusIndex === 'number' && options?.source !== 'pointer') {
        queueRowFocus(focusIndex, options?.source);
      }
      if (readOnly) {
        onStartEdit?.();
      }
    },
    [onStartEdit, queueRowFocus, readOnly],
  );

  const makeItem = React.useCallback((text = ''): ListItemModel => ({
    id: `${blockId}-item-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
    text,
  }), [blockId]);

  const insertItemAfter = React.useCallback(
    (index: number) => {
      clearPendingAllEmptyExit();
      const nextItems = [...items];
      nextItems.splice(index + 1, 0, makeItem());
      commitItems(nextItems);
      queueRowFocus(Math.min(index + 1, nextItems.length - 1));
    },
    [clearPendingAllEmptyExit, commitItems, items, makeItem, queueRowFocus],
  );

  const focusRowFromPointer = React.useCallback(
    (index: number, event: React.MouseEvent<HTMLDivElement>) => {
      if (event.button !== 0) {
        return;
      }
      const target = event.target as HTMLElement | null;
      if (target?.closest('[contenteditable="true"]')) {
        return;
      }
      const editorId = buildRowId(index);
      const editorHandle = getBlockEditorHandle(editorId);
      if (!editorHandle) {
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      const pointerOffset = editorHandle.getOffsetFromPoint?.(event.clientX, event.clientY);
      announceFocusIntent('pointer', editorId, {
        ttlMs: 600,
        payload: typeof pointerOffset === 'number' ? { offset: pointerOffset } : undefined,
        source: 'list-editor.pointer-capture',
      });

      const scheduleFocus = () => {
        requestAnimationFrame(() => {
          editorHandle.focusFromPoint?.(event.clientX, event.clientY);
        });
      };

      if (readOnly) {
        ensureEditingMode(index, { source: 'pointer' });
        requestAnimationFrame(() => {
          requestAnimationFrame(scheduleFocus);
        });
        return;
      }
      scheduleFocus();
    },
    [buildRowId, ensureEditingMode, readOnly],
  );

  const exitListCompletely = React.useCallback(() => {
    clearPendingAllEmptyExit();
    onExitEdit();
    onDeleteEmptyBlock?.();
  }, [clearPendingAllEmptyExit, onDeleteEmptyBlock, onExitEdit]);

  const exitListAndCreateSibling = React.useCallback(
    (index: number) => {
      clearPendingAllEmptyExit();
      const isOnlyItem = items.length <= 1;
      if (isOnlyItem) {
        exitListCompletely();
        return;
      }
      const nextItems = items.filter((_, idx) => idx !== index);
      commitItems(nextItems);
      onExitEdit();
      onCreateSiblingBlock?.();
    },
    [clearPendingAllEmptyExit, commitItems, exitListCompletely, items, onCreateSiblingBlock, onExitEdit],
  );

  const removeItem = React.useCallback(
    (index: number) => {
      clearPendingAllEmptyExit();
      if (items.length <= 1) {
        commitItems([makeItem('')]);
        queueRowFocus(0);
        return;
      }
      const nextItems = items.filter((_, idx) => idx !== index);
      commitItems(nextItems);
      queueRowFocus(Math.max(0, Math.min(index, nextItems.length - 1)));
    },
    [clearPendingAllEmptyExit, commitItems, items, makeItem, queueRowFocus],
  );

  const updateItem = React.useCallback(
    (index: number, text: string) => {
      const nextItems = [...items];
      nextItems[index] = { ...nextItems[index], text };
      commitItems(nextItems);
      if (normalizeForEmptyCheck(text)) {
        clearPendingAllEmptyExit();
      }
    },
    [clearPendingAllEmptyExit, commitItems, items],
  );

  const focusSibling = React.useCallback(
    (index: number, direction: 'prev' | 'next') => {
      const nextIndex = direction === 'prev' ? index - 1 : index + 1;
      if (nextIndex >= 0 && nextIndex < items.length) {
        queueRowFocus(nextIndex);
        return true;
      }
      return false;
    },
    [items.length, queueRowFocus],
  );

  const handleKeyboardDecision = React.useCallback(
    (index: number, intent: KeyboardIntent, decision: KeyboardAction) => {
      if (decision === 'list-insert-item') {
        insertItemAfter(index);
        return true;
      }
      if (decision === 'list-remove-item') {
        removeItem(index);
        return true;
      }
      if (decision === 'list-exit') {
        if (intent === 'enter' && allItemsEmpty && !pendingAllEmptyExitRef.current) {
          insertItemAfter(index);
          pendingAllEmptyExitRef.current = true;
          return true;
        }
        pendingAllEmptyExitRef.current = false;
        if (allItemsEmpty) {
          exitListCompletely();
          return true;
        }
        exitListAndCreateSibling(index);
        return true;
      }
      return false;
    },
    [allItemsEmpty, exitListAndCreateSibling, exitListCompletely, insertItemAfter, removeItem],
  );

  const handleBlurCapture = (event: React.FocusEvent<HTMLDivElement>) => {
    const next = event.relatedTarget as Node | null;
    if (next && rootRef.current?.contains(next)) {
      return;
    }
    onExitEdit();
  };

  return (
    <div ref={rootRef} className={`${styles.todoList} ${styles.listBlock}`} onBlurCapture={handleBlurCapture}>
      {items.map((item, index) => {
        const marker = ordered ? index + 1 : '•';
        const markerClass = ordered ? styles.inlineMarkerOrdered : styles.inlineMarkerBullet;
        const editorId = `${blockId}-item-${index}`;
        return (
          <div
            key={editorId}
            className={`${styles.inlineRow} ${styles.todoEditorRow}`}
            onMouseDownCapture={(event) => focusRowFromPointer(index, event)}
          >
            <span className={`${styles.inlineMarker} ${markerClass}`}>{marker}</span>
            <div className={styles.inlineEditorText}>
              <ParagraphEditor
                blockId={editorId}
                value={item.text ?? ''}
                placeholder={itemPlaceholder}
                readOnly={readOnly}
                autoFocus={!readOnly && pendingFocusIndex === index}
                onChange={(text) => updateItem(index, text)}
                onSubmit={() => insertItemAfter(index)}
                getKeyboardContext={() => buildKeyboardContext(index)}
                onKeyboardDecision={({ intent, decision }) => handleKeyboardDecision(index, intent, decision)}
                onExitEdit={onExitEdit}
                onSoftBreak={onSoftBreak}
                onDeleteEmptyBlock={() => removeItem(index)}
                onStartEdit={() => ensureEditingMode(index)}
                onFocusPrev={() => {
                  if (!focusSibling(index, 'prev')) {
                    onFocusPrev?.();
                  }
                }}
                onFocusNext={() => {
                  if (!focusSibling(index, 'next')) {
                    onFocusNext?.();
                  }
                }}
                suppressBlurExit
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
