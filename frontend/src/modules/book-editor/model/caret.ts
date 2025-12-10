import React from 'react';
import { getActiveSelection, getCaretRectFromSelection } from './caretDomUtils';

// Plan130: caret tracking is opt-in. We only attach listeners when inline UI needs
// caret positioning (e.g., slash menu、mini toolbar)。
export interface CaretRect {
  top: number;
  left: number;
  height: number;
  width: number;
}

export const getCaretRect = (): CaretRect | null => {
  const rect = getCaretRectFromSelection(getActiveSelection());
  if (!rect) {
    return null;
  }
  return {
    top: rect.top,
    left: rect.left,
    height: rect.height,
    width: rect.width,
  };
};

export const useScopedCaretTracker = (
  enabled: boolean,
  scopeRef?: React.RefObject<HTMLElement | null>
): CaretRect | null => {
  const [caretRect, setCaretRect] = React.useState<CaretRect | null>(null);

  React.useEffect(() => {
    if (!enabled) {
      setCaretRect(null);
      return;
    }

    const handleSelectionChange = () => {
      const selection = getActiveSelection();
      if (!selection || selection.rangeCount === 0) {
        setCaretRect(null);
        return;
      }
      const anchorNode = selection.anchorNode;
      if (scopeRef?.current && anchorNode && !scopeRef.current.contains(anchorNode)) {
        return;
      }
      setCaretRect(getCaretRect());
    };

    handleSelectionChange();
    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [enabled, scopeRef]);

  return caretRect;
};
