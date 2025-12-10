'use client';
import React from 'react';

type Item = {
  id: string;
  color?: string;
  label?: string;
  tooltip?: string;
  onClick?: () => void;
  href?: string;
};

export default function BookmarkRail({
  items = [],
  top = 96,
  leftOffset = 8,
  currentId,
}: {
  items?: Item[];
  top?: number;
  leftOffset?: number;
  currentId?: string;
}) {
  if (!items?.length) return null;

  const style: React.CSSProperties = {
    top,
    // 兜底：无 --sidebar-w 时按 72px（收起宽度）计算
    left: `calc(var(--sidebar-w, 72px) + ${leftOffset}px)`,
  };

  return (
    <div className="bookmark-rail" style={style} aria-label="bookmark-rail">
      {items.map((it) => (
        <button
          key={it.id}
          className="bm"
          aria-current={currentId === it.id ? 'true' : 'false'}
          style={{ ['--bm-color' as any]: it.color || '#8b5cf6' }}
          title={it.tooltip || it.label || ''}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            it.onClick?.();
            if (it.href) {
              try {
                const target = document.querySelector(it.href) as HTMLElement | null;
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
              } catch {}
            }
          }}
        />
      ))}
    </div>
  );
}
