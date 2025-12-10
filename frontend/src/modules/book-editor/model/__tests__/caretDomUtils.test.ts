import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  getTextContentLength,
  resolveNodeOffsetFromTextOffset,
  placeCaretAtTextOffset,
  getCaretOffsetWithin,
  offsetFromPoint,
} from '../caretDomUtils';

describe('caretDomUtils', () => {
  const createEditable = (text = '') => {
    const element = document.createElement('div');
    element.contentEditable = 'true';
    element.textContent = text;
    document.body.appendChild(element);
    return element;
  };

  beforeEach(() => {
    document.body.innerHTML = '';
    const selection = window.getSelection();
    selection?.removeAllRanges();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    const selection = window.getSelection();
    selection?.removeAllRanges();
  });

  it('resolves node offset from absolute offset', () => {
    const root = createEditable('hello world');

    const position = resolveNodeOffsetFromTextOffset(root, 4);

    expect(position).not.toBeNull();
    expect(position?.offset).toBe(4);
    expect(position?.node.textContent).toContain('hello world');
  });

  it('returns zero text length for missing editable root', () => {
    expect(getTextContentLength(null)).toBe(0);
  });

  it('places caret at a given text offset and tracks selection offsets', () => {
    const root = createEditable('abcd');
    const focusSpy = vi.fn();
    // jsdom does not implement focus on divs, so stub it for verification.
    (root as HTMLElement).focus = focusSpy;

    const appliedOffset = placeCaretAtTextOffset(root, 2);

    expect(appliedOffset).toBe(2);
    expect(getCaretOffsetWithin(root)).toBe(2);
    expect(focusSpy).toHaveBeenCalledTimes(1);
  });

  it('derives absolute offset from pointer coordinates when caretRangeFromPoint is available', () => {
    const root = createEditable('lorem ipsum');
    const doc = root.ownerDocument as Document & {
      caretRangeFromPoint?: (x: number, y: number) => Range | null;
    };
    const range = doc.createRange();
    const textNode = root.firstChild as Text;
    range.setStart(textNode, 5);
    range.collapse(true);
    doc.caretRangeFromPoint = vi.fn().mockReturnValue(range);

    const result = offsetFromPoint(root, 10, 12);

    expect(doc.caretRangeFromPoint).toHaveBeenCalledWith(10, 12);
    expect(result).toEqual({ absoluteOffset: 5 });

    doc.caretRangeFromPoint = undefined;
  });
});
