import type { BlockKind } from '@/entities/block';

const ZERO_WIDTH_PATTERN = /[\u00A0\u200B\uFEFF]/g;
const NBSP_PATTERN = /\u00A0/g;

const normalizeText = (value: string | null | undefined): string => {
  if (!value) {
    return '';
  }
  return value.replace(NBSP_PATTERN, ' ');
};

const sanitize = (value: string): string => value.replace(ZERO_WIDTH_PATTERN, '');

const BULLET_PATTERN = /^[-*+]$/;
const NUMBERED_PATTERN = /^\d+(?:[.)])$/;
const TODO_PATTERN = /^[-*+]\s*\[(?:\s|x|X)\]$/;

export const detectMarkdownShortcut = (text: string | null | undefined, caretOffset: number | null): BlockKind | null => {
  if (caretOffset == null) {
    return null;
  }
  const normalized = sanitize(normalizeText(text));
  const before = normalized.slice(0, caretOffset);
  const after = normalized.slice(caretOffset);
  if (after.trim().length > 0) {
    return null;
  }
  const trimmed = before.trimEnd();
  if (!trimmed) {
    return null;
  }
  if (BULLET_PATTERN.test(trimmed)) {
    return 'bulleted_list';
  }
  if (NUMBERED_PATTERN.test(trimmed)) {
    return 'numbered_list';
  }
  if (TODO_PATTERN.test(trimmed)) {
    return 'todo_list';
  }
  if (trimmed === '>') {
    return 'quote';
  }
  return null;
};

export const isCaretInEmptySegment = (text: string | null | undefined, caretOffset: number | null): boolean => {
  if (caretOffset == null) {
    return false;
  }
  const sanitized = sanitize(normalizeText(text));
  if (!sanitized) {
    return true;
  }
  const before = sanitized.slice(0, caretOffset);
  const lastBreak = Math.max(before.lastIndexOf('\n'), before.lastIndexOf('\r'));
  const segment = before.slice(lastBreak + 1).trim();
  return segment.length === 0;
};
