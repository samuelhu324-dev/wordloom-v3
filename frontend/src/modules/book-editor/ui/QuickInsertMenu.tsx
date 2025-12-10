'use client';

import React from 'react';
import { createPortal } from 'react-dom';
import type { QuickInsertAction } from '../model/quickActions';
import styles from './bookEditor.module.css';
import { groupQuickInsertActions } from './quickInsertGroups';
import { useI18n } from '@/i18n/useI18n';

interface QuickInsertMenuProps {
  anchorRect: DOMRect | null;
  actions: QuickInsertAction[];
  onSelect: (action: QuickInsertAction) => void;
  onClose: () => void;
}

export const QuickInsertMenu: React.FC<QuickInsertMenuProps> = ({ anchorRect, actions, onSelect, onClose }) => {
  const [mounted, setMounted] = React.useState(false);
  const menuRef = React.useRef<HTMLDivElement | null>(null);
  const [positionStyle, setPositionStyle] = React.useState<{ top: number; left: number } | null>(null);
  const { t } = useI18n();
  const groupedActions = React.useMemo(() => groupQuickInsertActions(actions, t), [actions, t]);
  const transformLabel = React.useMemo(() => t('books.blocks.editor.quickMenu.meta.transform'), [t]);
  const insertLabel = React.useMemo(() => t('books.blocks.editor.quickMenu.meta.insert'), [t]);

  const updateMenuPosition = React.useCallback(() => {
    if (typeof window === 'undefined' || !menuRef.current) {
      return;
    }
    const menu = menuRef.current;
    const menuRect = menu.getBoundingClientRect();
    const fallbackLeft = window.innerWidth / 2;
    const fallbackTop = window.innerHeight / 2;
    const preferredAnchor = anchorRect ?? new DOMRect(fallbackLeft, fallbackTop, 0, 0);
    const anchorTop = preferredAnchor.top ?? fallbackTop;
    const anchorBottom = preferredAnchor.bottom ?? fallbackTop;
    let top = anchorBottom + 8;
    let left = preferredAnchor.left ?? fallbackLeft;
    const viewportPadding = 12;

    if (left + menuRect.width + viewportPadding > window.innerWidth) {
      left = Math.max(viewportPadding, window.innerWidth - viewportPadding - menuRect.width);
    }
    if (left < viewportPadding) {
      left = viewportPadding;
    }

    if (top + menuRect.height + viewportPadding > window.innerHeight) {
      top = Math.max(viewportPadding, anchorTop - menuRect.height - 8);
    }
    if (top < viewportPadding) {
      top = viewportPadding;
    }

    setPositionStyle({ top, left });
  }, [anchorRect]);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!mounted) return;
    const handleClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('mousedown', handleClick);
    document.addEventListener('keydown', handleKey);
    return () => {
      document.removeEventListener('mousedown', handleClick);
      document.removeEventListener('keydown', handleKey);
    };
  }, [mounted, onClose]);

  React.useLayoutEffect(() => {
    if (!mounted) return;
    updateMenuPosition();
  }, [mounted, updateMenuPosition, groupedActions.length]);

  if (!mounted) {
    return null;
  }
  const style: React.CSSProperties = positionStyle ?? { visibility: 'hidden' };

  return createPortal(
    <div className={styles.quickMenu} style={style} ref={menuRef} role="menu">
      <div className={styles.quickMenuGroups}>
        {groupedActions.map((group, groupIndex) => (
          <div key={group.title} className={styles.quickMenuGroup}>
            <p className={styles.quickMenuGroupTitle}>{group.title}</p>
            <ul className={styles.quickMenuList}>
              {group.actions.map((action) => (
                <li key={action.id}>
                  <button
                    type="button"
                    className={styles.quickMenuItem}
                    data-behavior={action.behavior}
                    onClick={() => onSelect(action)}
                  >
                    <div className={styles.quickMenuItemContent}>
                      <span className={styles.quickMenuItemLabel}>{action.label}</span>
                      <span className={styles.quickMenuHint}>{action.hint}</span>
                    </div>
                    <span className={styles.quickMenuItemMeta}>
                      {action.behavior === 'transform' ? transformLabel : insertLabel}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            {groupIndex < groupedActions.length - 1 && <div className={styles.quickMenuDivider} />}
          </div>
        ))}
      </div>
    </div>,
    document.body,
  );
};
