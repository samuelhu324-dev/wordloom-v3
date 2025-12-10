'use client';

import React from 'react';
import {
  clearFocusIntent,
  focusIntentStore,
  reportSelectionSnapshot,
  selectionStore,
  type FocusIntent,
  type SelectionEdge,
} from './selectionStore';
import {
  getCaretOffsetWithin,
  getCaretRectWithin,
  getSelectionWithin,
  getTextContentLength,
  offsetFromPoint,
  placeCaretAtTextOffset,
} from './caretDomUtils';

export interface UseBlockCaretControllerOptions {
  blockId: string;
  editableRef: React.RefObject<HTMLElement | null>;
  readOnly?: boolean;
  autoFocus?: boolean;
  focusPosition?: SelectionEdge;
}

export interface BlockCaretController {
  getCaretRect: () => DOMRect | null;
  getCaretOffset: () => number | null;
  isCaretAtEdge: (edge: SelectionEdge) => boolean;
  placeCaretAtOffset: (offset: number) => number | null;
  placeCaretAtEdge: (edge: SelectionEdge) => void;
  focusFromPoint: (clientX: number, clientY: number) => void;
  getOffsetFromPoint: (clientX: number, clientY: number) => number | null;
  publishSelectionSnapshot: (knownOffset?: number, knownLength?: number) => void;
  clearSelectionSnapshot: () => void;
}

const isBrowser = () => typeof window !== 'undefined';

export const useBlockCaretController = (options: UseBlockCaretControllerOptions): BlockCaretController => {
  const { blockId, editableRef, readOnly, autoFocus, focusPosition } = options;
  const prevReadOnlyRef = React.useRef(readOnly);

  const getRoot = React.useCallback(() => editableRef.current, [editableRef]);

  const getCaretRect = React.useCallback(() => {
    const root = getRoot();
    return root ? getCaretRectWithin(root) : null;
  }, [getRoot]);

  const getCaretOffset = React.useCallback(() => {
    const root = getRoot();
    return root ? getCaretOffsetWithin(root) : null;
  }, [getRoot]);

  const clearSelectionSnapshot = React.useCallback(() => {
    const snapshot = selectionStore.getSnapshot();
    if (snapshot?.blockId === blockId) {
      reportSelectionSnapshot(null);
    }
  }, [blockId]);

  const publishSelectionSnapshot = React.useCallback(
    (knownOffset?: number, knownLength?: number) => {
      const offset = typeof knownOffset === 'number' ? knownOffset : getCaretOffset();
      if (offset == null) {
        return;
      }
      const root = getRoot();
      const fallbackLength = root ? getTextContentLength(root) : 0;
      const textLength = typeof knownLength === 'number' ? knownLength : fallbackLength;
      reportSelectionSnapshot({
        blockId,
        offset,
        textLength,
        updatedAt: Date.now(),
      });
    },
    [blockId, getCaretOffset, getRoot],
  );

  const placeCaretAtOffset = React.useCallback(
    (offset: number) => {
      const root = getRoot();
      if (!root) {
        return null;
      }
      const appliedOffset = placeCaretAtTextOffset(root, offset);
      if (appliedOffset != null) {
        publishSelectionSnapshot(appliedOffset);
      }
      return appliedOffset;
    },
    [getRoot, publishSelectionSnapshot],
  );

  const placeCaretAtEdge = React.useCallback(
    (edge: SelectionEdge) => {
      if (edge === 'start') {
        placeCaretAtOffset(0);
        return;
      }
      const root = getRoot();
      if (!root) {
        return;
      }
      const length = getTextContentLength(root);
      placeCaretAtOffset(length);
    },
    [getRoot, placeCaretAtOffset],
  );

  const isCaretAtEdge = React.useCallback(
    (edge: SelectionEdge) => {
      const root = getRoot();
      if (!root) {
        return false;
      }
      const selection = getSelectionWithin(root);
      if (!selection || !selection.isCollapsed) {
        return false;
      }
      const range = selection.getRangeAt(0).cloneRange();
      const doc =
        range.commonAncestorContainer.ownerDocument ?? (typeof document !== 'undefined' ? document : null);
      if (!doc) {
        return false;
      }
      const comparator = doc.createRange();
      comparator.selectNodeContents(root);
      if (edge === 'start') {
        comparator.setEnd(range.startContainer, range.startOffset);
      } else {
        comparator.setStart(range.endContainer, range.endOffset);
      }
      return comparator.toString().length === 0;
    },
    [getRoot],
  );

  const focusFromPoint = React.useCallback(
    (clientX: number, clientY: number) => {
      const root = getRoot();
      if (!root) {
        return;
      }
      const result = offsetFromPoint(root, clientX, clientY);
      if (result) {
        placeCaretAtOffset(result.absoluteOffset);
        return;
      }
      if (typeof root.focus === 'function') {
        root.focus();
      }
    },
    [getRoot, placeCaretAtOffset],
  );

  const getOffsetFromPoint = React.useCallback(
    (clientX: number, clientY: number) => {
      const root = getRoot();
      if (!root) {
        return null;
      }
      const result = offsetFromPoint(root, clientX, clientY);
      return result?.absoluteOffset ?? null;
    },
    [getRoot],
  );

  const shouldSkipForIntent = React.useCallback(
    (intent: FocusIntent | null) => {
      if (!intent) {
        return false;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return true;
      }
      return false;
    },
    [blockId],
  );

  const maybeClearFocusIntent = React.useCallback(
    (intent: FocusIntent | null) => {
      if (!intent) {
        return;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return;
      }
      clearFocusIntent(intent.token);
    },
    [blockId],
  );

  const applyIntentPayload = React.useCallback(
    (intent: FocusIntent | null, fallbackEdge?: SelectionEdge) => {
      if (intent) {
        if (intent.targetId && intent.targetId !== blockId) {
          return false;
        }
        const payload = intent.payload;
        if (payload?.edge) {
          placeCaretAtEdge(payload.edge);
          return true;
        }
        if (typeof payload?.offset === 'number' && Number.isFinite(payload.offset)) {
          placeCaretAtOffset(payload.offset);
          return true;
        }
      }
      if (fallbackEdge) {
        placeCaretAtEdge(fallbackEdge);
        return true;
      }
      return false;
    },
    [blockId, placeCaretAtEdge, placeCaretAtOffset],
  );

  React.useEffect(() => {
    if (!autoFocus || readOnly) {
      return;
    }
    const intent = focusIntentStore.getIntent();
    if (shouldSkipForIntent(intent)) {
      return;
    }
    let caretFrame: number | null = null;
    const frame = isBrowser()
      ? window.requestAnimationFrame(() => {
          getRoot()?.focus();
          caretFrame = window.requestAnimationFrame(() => {
            applyIntentPayload(intent, focusPosition ?? 'start');
            maybeClearFocusIntent(intent);
          });
        })
      : null;
    return () => {
      if (frame != null && isBrowser()) {
        window.cancelAnimationFrame(frame);
      }
      if (caretFrame != null && isBrowser()) {
        window.cancelAnimationFrame(caretFrame);
      }
    };
  }, [applyIntentPayload, autoFocus, focusPosition, getRoot, maybeClearFocusIntent, readOnly, shouldSkipForIntent]);

  React.useEffect(() => {
    if (!focusPosition) {
      return;
    }
    if (typeof document === 'undefined') {
      return;
    }
    const root = getRoot();
    if (!root || document.activeElement !== root) {
      return;
    }
    const intent = focusIntentStore.getIntent();
    if (shouldSkipForIntent(intent)) {
      return;
    }
    applyIntentPayload(intent, focusPosition);
    maybeClearFocusIntent(intent);
  }, [applyIntentPayload, focusPosition, getRoot, maybeClearFocusIntent, shouldSkipForIntent]);

  React.useEffect(() => {
    let frame: number | null = null;
    if (prevReadOnlyRef.current && !readOnly) {
      const intent = focusIntentStore.getIntent();
      if (!shouldSkipForIntent(intent)) {
        frame = isBrowser()
          ? window.requestAnimationFrame(() => {
              getRoot()?.focus();
              applyIntentPayload(intent, focusPosition ?? 'start');
              maybeClearFocusIntent(intent);
            })
          : null;
      }
    }
    prevReadOnlyRef.current = readOnly;
    return () => {
      if (frame != null && isBrowser()) {
        window.cancelAnimationFrame(frame);
      }
    };
  }, [applyIntentPayload, focusPosition, getRoot, maybeClearFocusIntent, readOnly, shouldSkipForIntent]);

  React.useEffect(() => {
    if (readOnly) {
      return;
    }
    let raf: number | null = null;
    const unsubscribe = focusIntentStore.subscribe(() => {
      const intent = focusIntentStore.getIntent();
      if (!intent) {
        return;
      }
      if (intent.targetId && intent.targetId !== blockId) {
        return;
      }
      const root = getRoot();
      if (!root) {
        return;
      }
      if (typeof document !== 'undefined' && document.activeElement !== root) {
        root.focus();
      }
      if (raf != null && isBrowser()) {
        window.cancelAnimationFrame(raf);
      }
      raf = isBrowser()
        ? window.requestAnimationFrame(() => {
            const consumed = applyIntentPayload(intent, 'start');
            if (consumed) {
              maybeClearFocusIntent(intent);
            }
          })
        : null;
    });
    return () => {
      unsubscribe();
      if (raf != null && isBrowser()) {
        window.cancelAnimationFrame(raf);
      }
    };
  }, [applyIntentPayload, blockId, getRoot, maybeClearFocusIntent, readOnly]);

  React.useEffect(() => {
    if (typeof document === 'undefined') {
      return;
    }
    const handleSelectionChange = () => {
      const root = getRoot();
      if (!root) {
        return;
      }
      const selection = getSelectionWithin(root);
      if (!selection) {
        clearSelectionSnapshot();
        return;
      }
      publishSelectionSnapshot();
    };
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange);
      clearSelectionSnapshot();
    };
  }, [clearSelectionSnapshot, getRoot, publishSelectionSnapshot]);

  return React.useMemo(
    () => ({
      getCaretRect,
      getCaretOffset,
      isCaretAtEdge,
      placeCaretAtOffset,
      placeCaretAtEdge,
      focusFromPoint,
      getOffsetFromPoint,
      publishSelectionSnapshot,
      clearSelectionSnapshot,
    }),
    [
      clearSelectionSnapshot,
      focusFromPoint,
      getOffsetFromPoint,
      getCaretOffset,
      getCaretRect,
      isCaretAtEdge,
      placeCaretAtEdge,
      placeCaretAtOffset,
      publishSelectionSnapshot,
    ],
  );
};
