"use client";

import { reportBlockEditorCaretIntent } from '@/shared/telemetry/blockEditorTelemetry';

export type SelectionEdge = 'start' | 'end';

export interface SelectionSnapshot {
  blockId: string;
  offset: number;
  textLength: number;
  updatedAt: number;
}

export type FocusIntentKind = 'pointer' | 'keyboard' | 'initial';

export interface FocusIntentPayload {
  edge?: SelectionEdge;
  offset?: number;
}

export interface FocusIntent {
  kind: FocusIntentKind;
  targetId: string | null;
  token: number;
  issuedAt: number;
  payload?: FocusIntentPayload;
  source?: string;
}

const selectionListeners = new Set<() => void>();
let currentSelectionSnapshot: SelectionSnapshot | null = null;

const focusListeners = new Set<() => void>();
let currentFocusIntent: FocusIntent | null = null;
let focusCounter = 0;

const focusEmit = () => {
  focusListeners.forEach((listener) => listener());
};

const setSelectionSnapshot = (snapshot: SelectionSnapshot | null) => {
  currentSelectionSnapshot = snapshot;
  selectionListeners.forEach((listener) => listener());
};

const setFocusIntentState = (intent: FocusIntent | null) => {
  currentFocusIntent = intent;
  focusEmit();
};

export const selectionStore = {
  getSnapshot: () => currentSelectionSnapshot,
  subscribe: (listener: () => void) => {
    selectionListeners.add(listener);
    return () => {
      selectionListeners.delete(listener);
    };
  },
};

export const reportSelectionSnapshot = (snapshot: SelectionSnapshot | null) => {
  setSelectionSnapshot(snapshot);
};

export const focusIntentStore = {
  getIntent: () => currentFocusIntent,
  subscribe: (listener: () => void) => {
    focusListeners.add(listener);
    return () => {
      focusListeners.delete(listener);
    };
  },
  issue: (kind: FocusIntentKind, targetId?: string | null, payload?: FocusIntentPayload, source?: string) => {
    const token = ++focusCounter;
    setFocusIntentState({
      kind,
      targetId: targetId ?? null,
      token,
      issuedAt: Date.now(),
      payload,
      source,
    });
    return token;
  },
  clear: (token?: number) => {
    if (!token || (currentFocusIntent && currentFocusIntent.token === token)) {
      setFocusIntentState(null);
    }
  },
};

export interface AnnounceFocusIntentOptions {
  ttlMs?: number;
  payload?: FocusIntentPayload;
  source?: string;
}

const scheduleIntentExpiry = (token: number, ttlMs?: number) => {
  if (!ttlMs) {
    return;
  }
  const clear = () => focusIntentStore.clear(token);
  if (typeof window !== 'undefined' && typeof window.setTimeout === 'function') {
    window.setTimeout(clear, ttlMs);
    return;
  }
  setTimeout(clear, ttlMs);
};

export const announceFocusIntent = (
  kind: FocusIntentKind,
  targetId?: string | null,
  options?: AnnounceFocusIntentOptions,
) => {
  const token = focusIntentStore.issue(kind, targetId, options?.payload, options?.source);
  reportBlockEditorCaretIntent({
    kind,
    targetId: targetId ?? null,
    payload: options?.payload,
    source: options?.source,
  });
  scheduleIntentExpiry(token, options?.ttlMs);
  return token;
};

export const clearFocusIntent = (token?: number) => focusIntentStore.clear(token);
