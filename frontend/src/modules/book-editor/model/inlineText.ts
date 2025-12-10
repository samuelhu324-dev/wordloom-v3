const WINDOWS_LINE_BREAK = /\r\n/g;
const NBSP_PATTERN = /\u00A0/g;
const ZERO_WIDTH_PATTERN = /[\u200B\uFEFF]/g;

const normalizeInlineText = (value: string): string => {
  if (!value) {
    return '';
  }
  let normalized = value.replace(WINDOWS_LINE_BREAK, '\n');
  normalized = normalized.replace(NBSP_PATTERN, ' ');
  normalized = normalized.replace(ZERO_WIDTH_PATTERN, '');
  return normalized;
};

export const extractInlineTextFromEditable = (root: HTMLElement | null): string => {
  if (!root) {
    return '';
  }
  const clone = root.cloneNode(true) as HTMLElement;
  clone.querySelectorAll('br').forEach((br) => {
    br.replaceWith('\n');
  });
  const raw = clone.textContent ?? '';
  return normalizeInlineText(raw);
};

const clampOffset = (offset: number, max: number): number => {
  if (Number.isNaN(offset)) {
    return max;
  }
  if (offset < 0) {
    return 0;
  }
  if (offset > max) {
    return max;
  }
  return offset;
};

export interface SoftBreakInsertionResult {
  text: string;
  caretOffset: number;
}

export const insertSoftBreakAt = (text: string, caretOffset?: number | null): SoftBreakInsertionResult => {
  const base = typeof text === 'string' ? text : '';
  const safeOffset = clampOffset(typeof caretOffset === 'number' ? caretOffset : base.length, base.length);
  const nextText = `${base.slice(0, safeOffset)}\n${base.slice(safeOffset)}`;
  return {
    text: nextText,
    caretOffset: safeOffset + 1,
  };
};
