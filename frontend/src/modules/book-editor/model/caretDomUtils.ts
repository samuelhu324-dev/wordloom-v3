const SHOW_TEXT = typeof NodeFilter !== 'undefined' ? NodeFilter.SHOW_TEXT : 4;

export interface NodeOffset {
  node: Node;
  offset: number;
}

export interface OffsetFromPointResult {
  absoluteOffset: number;
}

const isBrowser = () => typeof window !== 'undefined';

const clamp = (value: number, min: number, max: number) => {
  if (value < min) return min;
  if (value > max) return max;
  return value;
};

const resolveDocument = (root?: HTMLElement | null): Document | null => {
  if (root?.ownerDocument) {
    return root.ownerDocument;
  }
  if (typeof document !== 'undefined') {
    return document;
  }
  return null;
};

const getSelectionFromDocument = (doc: Document | null): Selection | null => {
  if (!doc) {
    return null;
  }
  if (typeof doc.getSelection === 'function') {
    return doc.getSelection();
  }
  if (!isBrowser() || typeof window.getSelection !== 'function') {
    return null;
  }
  const selection = window.getSelection();
  return selection ?? null;
};

export const getActiveSelection = (): Selection | null => getSelectionFromDocument(resolveDocument(null));

export const getSelectionWithin = (root: HTMLElement | null): Selection | null => {
  if (!root) {
    return null;
  }
  const selection = getSelectionFromDocument(resolveDocument(root));
  if (!selection || selection.rangeCount === 0) {
    return null;
  }
  const anchor = selection.anchorNode;
  if (!anchor || !root.contains(anchor)) {
    return null;
  }
  return selection;
};

export const getCaretRectFromSelection = (selection: Selection | null): DOMRect | null => {
  if (!selection || selection.rangeCount === 0) {
    return null;
  }
  const range = selection.getRangeAt(0).cloneRange();
  range.collapse(true);
  const rects = range.getClientRects();
  if (rects.length > 0) {
    return rects[0];
  }
  return range.getBoundingClientRect();
};

export const getCaretRectWithin = (root: HTMLElement | null): DOMRect | null => {
  const selection = getSelectionWithin(root);
  return getCaretRectFromSelection(selection);
};

export const getTextContentLength = (root: HTMLElement | null): number => {
  if (!root) {
    return 0;
  }
  return root.textContent?.length ?? 0;
};

export const computeAbsoluteOffset = (root: HTMLElement | null, position: NodeOffset | null): number | null => {
  if (!root || !position) {
    return null;
  }
  const doc = resolveDocument(root);
  if (!doc) {
    return null;
  }
  const range = doc.createRange();
  range.selectNodeContents(root);
  try {
    range.setEnd(position.node, position.offset);
  } catch (error) {
    return null;
  }
  return range.toString().length;
};

export const getCaretOffsetWithin = (root: HTMLElement | null): number | null => {
  const selection = getSelectionWithin(root);
  if (!selection) {
    return null;
  }
  const position: NodeOffset = {
    node: selection.anchorNode!,
    offset: selection.anchorOffset,
  };
  return computeAbsoluteOffset(root, position);
};

const ensureTextNode = (node: Node, doc: Document): Node => {
  if (node.nodeType === Node.TEXT_NODE) {
    return node;
  }
  if (node.childNodes.length === 0) {
    const filler = doc.createTextNode('');
    node.appendChild(filler);
    return filler;
  }
  const child = node.childNodes[0];
  if (!child) {
    return ensureTextNode(node, doc);
  }
  return ensureTextNode(child, doc);
};

export const resolveNodeOffsetFromTextOffset = (root: HTMLElement | null, targetOffset: number): NodeOffset | null => {
  if (!root) {
    return null;
  }
  const doc = resolveDocument(root);
  if (!doc) {
    return null;
  }
  const totalLength = getTextContentLength(root);
  const clampedOffset = clamp(targetOffset, 0, totalLength);
  const walker = doc.createTreeWalker(root, SHOW_TEXT, null);
  let remaining = clampedOffset;
  let lastTextNode: Node | null = null;
  while (walker.nextNode()) {
    const textNode = walker.currentNode;
    lastTextNode = textNode;
    const length = textNode.textContent?.length ?? 0;
    if (remaining <= length) {
      return { node: textNode, offset: remaining };
    }
    remaining -= length;
  }
  if (lastTextNode) {
    const length = lastTextNode.textContent?.length ?? 0;
    return { node: lastTextNode, offset: length };
  }
  const fallback = doc.createTextNode('');
  root.appendChild(fallback);
  return { node: fallback, offset: 0 };
};

export const placeCaretAtNodeOffset = (
  root: HTMLElement | null,
  position: NodeOffset | null,
  options?: { focus?: boolean },
): boolean => {
  if (!root || !position) {
    return false;
  }
  const doc = resolveDocument(root);
  if (!doc) {
    return false;
  }
  const selection = getSelectionFromDocument(doc);
  if (!selection) {
    return false;
  }
  const targetNode = ensureTextNode(position.node, doc);
  const nodeLength = targetNode.textContent?.length ?? 0;
  const safeOffset = clamp(position.offset, 0, nodeLength);
  const range = doc.createRange();
  range.setStart(targetNode, safeOffset);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
  if (options?.focus ?? true) {
    if (typeof root.focus === 'function') {
      root.focus();
    }
  }
  return true;
};

export const placeCaretAtTextOffset = (
  root: HTMLElement | null,
  offset: number,
  options?: { focus?: boolean },
): number | null => {
  const position = resolveNodeOffsetFromTextOffset(root, offset);
  if (!position) {
    return null;
  }
  const success = placeCaretAtNodeOffset(root, position, options);
  return success ? computeAbsoluteOffset(root, position) : null;
};

export const offsetFromPoint = (root: HTMLElement | null, clientX: number, clientY: number): OffsetFromPointResult | null => {
  if (!root) {
    return null;
  }
  const doc = resolveDocument(root) as (Document & {
    caretRangeFromPoint?: (x: number, y: number) => Range | null;
    caretPositionFromPoint?: (x: number, y: number) => { offsetNode: Node; offset: number } | null;
  }) | null;
  if (!doc) {
    return null;
  }
  let range: Range | null = null;
  if (typeof doc.caretRangeFromPoint === 'function') {
    range = doc.caretRangeFromPoint(clientX, clientY);
  } else if (typeof doc.caretPositionFromPoint === 'function') {
    const position = doc.caretPositionFromPoint(clientX, clientY);
    if (position) {
      range = doc.createRange();
      range.setStart(position.offsetNode, position.offset);
      range.collapse(true);
    }
  }
  if (!range) {
    return null;
  }
  const startNode = range.startContainer;
  if (!root.contains(startNode)) {
    return null;
  }
  const absoluteOffset = computeAbsoluteOffset(root, { node: range.startContainer, offset: range.startOffset });
  if (absoluteOffset == null) {
    return null;
  }
  return { absoluteOffset };
};
