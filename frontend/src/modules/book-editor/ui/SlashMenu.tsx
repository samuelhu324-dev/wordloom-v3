'use client';

import React from 'react';
import type { QuickInsertAction } from '../model/quickActions';
import styles from './bookEditor.module.css';
import { groupQuickInsertActions } from './quickInsertGroups';
import { useI18n } from '@/i18n/useI18n';

interface SlashMenuProps {
  x: number;
  y: number;
  actions: QuickInsertAction[];
  onSelect: (action: QuickInsertAction) => void;
  onClose: () => void;
}

export const SlashMenu: React.FC<SlashMenuProps> = ({ x, y, actions, onSelect, onClose }) => {
  const menuRef = React.useRef<HTMLDivElement | null>(null);
  const { t } = useI18n();
  const groupedActions = React.useMemo(() => groupQuickInsertActions(actions, t), [actions, t]);
  const transformLabel = React.useMemo(() => t('books.blocks.editor.quickMenu.meta.transform'), [t]);
  const insertLabel = React.useMemo(() => t('books.blocks.editor.quickMenu.meta.insert'), [t]);
  const [positionStyle, setPositionStyle] = React.useState<{ left: number; top: number }>({ left: x, top: y });

  React.useEffect(() => {
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };
    const handleClick = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleKey);
    document.addEventListener('mousedown', handleClick);
    return () => {
      document.removeEventListener('keydown', handleKey);
      document.removeEventListener('mousedown', handleClick);
    };
  }, [onClose]);

  React.useLayoutEffect(() => {
    if (!menuRef.current) {
      setPositionStyle({ left: x, top: y });
      return;
    }
    const parent = menuRef.current.offsetParent as HTMLElement | null;
    const menuRect = menuRef.current.getBoundingClientRect();
    const parentRect = parent?.getBoundingClientRect();
    let nextLeft = x;
    let nextTop = y;
    const padding = 8;

    if (parentRect) {
      const overflowRight = menuRect.right - parentRect.right;
      if (overflowRight > 0) {
        nextLeft = Math.max(padding, nextLeft - overflowRight);
      } else if (menuRect.left < parentRect.left) {
        nextLeft = Math.max(padding, nextLeft + (parentRect.left - menuRect.left));
      }

      const overflowBottom = menuRect.bottom - parentRect.bottom;
      if (overflowBottom > 0) {
        nextTop = Math.max(padding, nextTop - overflowBottom);
      } else if (menuRect.top < parentRect.top) {
        nextTop = Math.max(padding, nextTop + (parentRect.top - menuRect.top));
      }
    }

    setPositionStyle({ left: nextLeft, top: nextTop });
  }, [x, y]);

  return (
    <div
      ref={menuRef}
      className={styles.slashMenu}
      style={positionStyle}
      role="menu"
    >
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
    </div>
  );
};
