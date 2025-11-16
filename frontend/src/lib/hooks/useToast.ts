/**
 * useToast Hook
 * Toast/Notification system for user feedback
 * Integrates success, error, warning, and info notifications
 */

'use client';

import { useState, useCallback } from 'react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  description?: string;
  duration?: number; // milliseconds, 0 = persistent
}

interface ToastState {
  toasts: Toast[];
}

/**
 * Global toast store
 * In a real app, this would be a context or state management library
 */
let toastState: ToastState = {
  toasts: [],
};

let listeners: ((state: ToastState) => void)[] = [];

/**
 * Subscribe to toast changes
 */
function subscribe(listener: (state: ToastState) => void) {
  listeners.push(listener);
  return () => {
    listeners = listeners.filter((l) => l !== listener);
  };
}

/**
 * Notify all listeners of state change
 */
function notifyListeners() {
  listeners.forEach((listener) => listener(toastState));
}

/**
 * Generate unique toast ID
 */
function generateId(): string {
  return `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Add toast to store
 */
function addToast(toast: Omit<Toast, 'id'>): string {
  const id = generateId();
  const newToast: Toast = { id, ...toast };
  toastState.toasts.push(newToast);
  notifyListeners();

  // Auto-remove after duration
  if (toast.duration !== 0) {
    const duration = toast.duration || 3000; // default 3 seconds
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }

  return id;
}

/**
 * Remove toast from store
 */
function removeToast(id: string) {
  toastState.toasts = toastState.toasts.filter((t) => t.id !== id);
  notifyListeners();
}

/**
 * Clear all toasts
 */
function clearToasts() {
  toastState.toasts = [];
  notifyListeners();
}

/**
 * useToast Hook
 * Provides methods to show toasts to the user
 *
 * Usage:
 * ```
 * const toast = useToast();
 * toast.success({ message: 'Created successfully!' });
 * toast.error({ message: 'Error occurred', description: 'Please try again' });
 * ```
 */
export function useToast() {
  const [, setState] = useState<ToastState>(toastState);

  // Subscribe to toast changes on mount
  useState(() => {
    return subscribe((newState) => {
      setState(newState);
    });
  })[1];

  return {
    /**
     * Show success toast
     */
    success: useCallback(
      (params: { message: string; description?: string; duration?: number }) => {
        return addToast({
          type: 'success',
          message: params.message,
          description: params.description,
          duration: params.duration || 3000,
        });
      },
      []
    ),

    /**
     * Show error toast
     */
    error: useCallback(
      (params: { message: string; description?: string; duration?: number }) => {
        return addToast({
          type: 'error',
          message: params.message,
          description: params.description,
          duration: params.duration || 5000, // longer duration for errors
        });
      },
      []
    ),

    /**
     * Show warning toast
     */
    warning: useCallback(
      (params: { message: string; description?: string; duration?: number }) => {
        return addToast({
          type: 'warning',
          message: params.message,
          description: params.description,
          duration: params.duration || 4000,
        });
      },
      []
    ),

    /**
     * Show info toast
     */
    info: useCallback(
      (params: { message: string; description?: string; duration?: number }) => {
        return addToast({
          type: 'info',
          message: params.message,
          description: params.description,
          duration: params.duration || 3000,
        });
      },
      []
    ),

    /**
     * Close a specific toast
     */
    close: useCallback((id: string) => {
      removeToast(id);
    }, []),

    /**
     * Close all toasts
     */
    closeAll: useCallback(() => {
      clearToasts();
    }, []),

    /**
     * Get current toasts (for rendering)
     */
    toasts: toastState.toasts,
  };
}


