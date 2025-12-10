import { getSelectionWithin } from './caretDomUtils';

export interface SlashMenuAnchorPoint {
  x: number;
  y: number;
}

const OFFSET_Y = 4;
const OFFSET_X = 0;

/**
 * Computes the slash menu anchor relative to the provided editor root element.
 * Returns null when the current selection is missing, outside of the editor,
 * or otherwise unusable.
 */
export function getSlashMenuAnchor(editorRoot: HTMLElement): SlashMenuAnchorPoint | null {
  if (!editorRoot) {
    return null;
  }

  const selection = getSelectionWithin(editorRoot);
  if (!selection || selection.rangeCount === 0) {
    return null;
  }

  const range = selection.getRangeAt(0).cloneRange();
  if (!range) {
    return null;
  }

  const startNode = range.startContainer;
  if (!editorRoot.contains(startNode)) {
    return null;
  }

  if (!range.collapsed) {
    range.collapse(false);
  }

  const rects = range.getClientRects();
  const caretRect = rects.length > 0 ? rects[0] : range.getBoundingClientRect();
  if (!caretRect) {
    return null;
  }

  const editorRect = editorRoot.getBoundingClientRect();
  const x = caretRect.left - editorRect.left + OFFSET_X;
  const y = caretRect.bottom - editorRect.top + OFFSET_Y;

  return { x, y };
}
