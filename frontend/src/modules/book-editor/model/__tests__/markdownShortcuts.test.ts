import { describe, it, expect } from 'vitest';
import { detectMarkdownShortcut, isCaretInEmptySegment } from '../markdownShortcuts';

describe('markdownShortcuts', () => {
  describe('detectMarkdownShortcut', () => {
    it('detects bulleted list markers', () => {
      expect(detectMarkdownShortcut('- ', 2)).toBe('bulleted_list');
      expect(detectMarkdownShortcut('*', 1)).toBe('bulleted_list');
    });

    it('detects numbered list markers', () => {
      expect(detectMarkdownShortcut('1.', 2)).toBe('numbered_list');
      expect(detectMarkdownShortcut('12)', 3)).toBe('numbered_list');
    });

    it('detects todo list markers', () => {
      expect(detectMarkdownShortcut('- [ ]', 5)).toBe('todo_list');
      expect(detectMarkdownShortcut('+ [x]', 6)).toBe('todo_list');
    });

    it('detects quote shortcut', () => {
      expect(detectMarkdownShortcut('>', 1)).toBe('quote');
    });

    it('requires caret to be at the end of the marker', () => {
      expect(detectMarkdownShortcut('> text', 2)).toBeNull();
      expect(detectMarkdownShortcut('- [ ] todo', 5)).toBeNull();
    });

    it('returns null when caret offset missing', () => {
      expect(detectMarkdownShortcut('>', null)).toBeNull();
    });
  });

  describe('isCaretInEmptySegment', () => {
    it('returns true when current segment only whitespace', () => {
      expect(isCaretInEmptySegment('foo\n\n', 5)).toBe(true);
    });

    it('returns false when text exists before caret in same segment', () => {
      expect(isCaretInEmptySegment('foo\nbar', 7)).toBe(false);
    });

    it('handles carriage returns', () => {
      expect(isCaretInEmptySegment('foo\r\n', 5)).toBe(true);
    });
  });
});
