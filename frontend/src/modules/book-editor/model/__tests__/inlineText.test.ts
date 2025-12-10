import { describe, it, expect } from 'vitest';
import { insertSoftBreakAt } from '../inlineText';

describe('insertSoftBreakAt', () => {
  it('inserts a soft break at the provided caret offset', () => {
    const result = insertSoftBreakAt('abcDEF', 3);
    expect(result.text).toBe('abc\nDEF');
    expect(result.caretOffset).toBe(4);
  });

  it('appends a soft break when caret offset is missing', () => {
    const result = insertSoftBreakAt('todo', undefined);
    expect(result.text).toBe('todo\n');
    expect(result.caretOffset).toBe(5);
  });
});
