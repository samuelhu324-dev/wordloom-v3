import React from 'react';

export interface AutoSizeTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  minRows?: number;
  maxRows?: number;
}

const useMergedRefs = <T,>(...refs: Array<React.Ref<T> | undefined>) => {
  return React.useCallback((value: T) => {
    refs.forEach((ref) => {
      if (!ref) return;
      if (typeof ref === 'function') {
        ref(value);
        return;
      }
      try {
        (ref as React.MutableRefObject<T>).current = value;
      } catch {
        // ignore assignment failures
      }
    });
  }, [refs]);
};

export const AutoSizeTextarea = React.forwardRef<HTMLTextAreaElement, AutoSizeTextareaProps>(
  ({ minRows = 1, maxRows = 3, value, style, ...rest }, forwardedRef) => {
    const innerRef = React.useRef<HTMLTextAreaElement | null>(null);
    const mergedRef = useMergedRefs(forwardedRef, innerRef);

    React.useLayoutEffect(() => {
      if (typeof window === 'undefined') return;
      const el = innerRef.current;
      if (!el) return;
      const nextValue = typeof value === 'string' ? value : el.value;
      if (typeof nextValue === 'undefined') return;
      el.style.height = '0px';
      const computed = el.scrollHeight;
      const computedStyle = window.getComputedStyle(el);
      const lineHeightRaw = computedStyle.lineHeight;
      const fontSize = Number.parseFloat(computedStyle.fontSize || '16');
      const resolvedLineHeight = (() => {
        if (lineHeightRaw && lineHeightRaw !== 'normal') {
          const parsed = Number.parseFloat(lineHeightRaw);
          if (Number.isFinite(parsed) && parsed > 0) {
            return parsed;
          }
        }
        if (Number.isFinite(fontSize)) {
          return fontSize * 1.4;
        }
        return 20;
      })();
      const minHeight = resolvedLineHeight * Math.max(1, minRows);
      const maxHeight = resolvedLineHeight * Math.max(minRows, maxRows);
      const nextHeight = Math.min(Math.max(computed, minHeight), maxHeight);
      el.style.height = `${nextHeight}px`;
    }, [value, minRows, maxRows]);

    return (
      <textarea
        {...rest}
        ref={mergedRef}
        style={{
          ...style,
          overflow: 'hidden',
          minHeight: 0,
        }}
        rows={minRows}
        value={value}
      />
    );
  }
);

AutoSizeTextarea.displayName = 'AutoSizeTextarea';
