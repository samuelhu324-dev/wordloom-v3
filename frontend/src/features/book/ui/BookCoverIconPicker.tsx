import { createPortal } from 'react-dom';
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { BookCoverIconId, BookCoverIconMeta } from '@/entities/book';
import { BOOK_COVER_ICON_CATALOG } from '@/entities/book';
import { getCoverIconComponent } from './bookCoverIcons';
import styles from './BookCoverIconPicker.module.css';
import { MoreHorizontal } from 'lucide-react';
import { useI18n } from '@/i18n/useI18n';

interface BookCoverIconPickerProps {
  value: BookCoverIconId | null;
  onChange: (value: BookCoverIconId | null) => void;
  disabled?: boolean;
}

const PRIMARY_ICON_IDS: BookCoverIconId[] = [
  'book-open-text',
  'star',
  'flask-conical',
  'banknote',
  'scale',
];

const ICON_META_MAP = BOOK_COVER_ICON_CATALOG.reduce<Record<BookCoverIconId, BookCoverIconMeta>>(
  (acc, item) => {
    acc[item.id] = item;
    return acc;
  },
  {} as Record<BookCoverIconId, BookCoverIconMeta>,
);

export const BookCoverIconPicker = ({ value, onChange, disabled = false }: BookCoverIconPickerProps) => {
  const { t } = useI18n();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [menuCoords, setMenuCoords] = useState<{ top: number; left: number; width: number } | null>(null);
  const [isPortalReady, setIsPortalReady] = useState(false);

  const primaryIcons = useMemo(
    () => PRIMARY_ICON_IDS.filter((id) => Boolean(ICON_META_MAP[id])),
    [],
  );

  const handlePrimarySelect = (iconId: BookCoverIconId) => {
    if (disabled) return;
    if (value === iconId) {
      onChange(null);
      return;
    }
    onChange(iconId);
  };

  const handleMenuSelect = (iconId: BookCoverIconId) => {
    if (disabled) return;
    onChange(iconId);
    setIsMenuOpen(false);
  };

  const handleToggleMenu = () => {
    if (disabled) return;
    setIsMenuOpen((prev) => !prev);
  };

  const handleClear = () => {
    if (disabled) return;
    onChange(null);
    setIsMenuOpen(false);
  };

  useEffect(() => {
    setIsPortalReady(true);
  }, []);

  useEffect(() => {
    if (!isMenuOpen) {
      setMenuCoords(null);
    }
  }, [isMenuOpen]);

  const updateMenuPosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const viewportPadding = 16;
    const verticalGap = 8;
    const panelWidth = Math.min(460, window.innerWidth - viewportPadding * 2);
    const maxLeft = window.innerWidth - viewportPadding - panelWidth;
    let left = rect.right - panelWidth;
    if (left < viewportPadding) {
      left = viewportPadding;
    }
    if (left > maxLeft) {
      left = maxLeft;
    }
    const maxTop = window.innerHeight - viewportPadding - 24;
    let top = rect.bottom + verticalGap;
    if (top > maxTop) {
      top = Math.max(viewportPadding, maxTop);
    }
    setMenuCoords({ top, left, width: panelWidth });
  }, []);

  useLayoutEffect(() => {
    if (!isMenuOpen) return undefined;
    updateMenuPosition();
    window.addEventListener('resize', updateMenuPosition);
    window.addEventListener('scroll', updateMenuPosition, true);
    return () => {
      window.removeEventListener('resize', updateMenuPosition);
      window.removeEventListener('scroll', updateMenuPosition, true);
    };
  }, [isMenuOpen, updateMenuPosition]);

  useEffect(() => {
    if (!isMenuOpen) return undefined;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (menuRef.current?.contains(target)) return;
      if (triggerRef.current?.contains(target)) return;
      setIsMenuOpen(false);
    };

    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEsc);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEsc);
    };
  }, [isMenuOpen]);

  return (
    <div className={styles.root} aria-disabled={disabled ? 'true' : undefined}>
      <div className={styles.primaryRow}>
        {primaryIcons.map((iconId) => {
          const IconComponent = getCoverIconComponent(iconId);
          const meta = ICON_META_MAP[iconId];
          const isActive = value === iconId;
          return (
            <button
              key={iconId}
              type="button"
              className={styles.primaryButton}
              data-active={isActive ? 'true' : undefined}
              onClick={() => handlePrimarySelect(iconId)}
              title={meta?.label}
              aria-label={meta?.label}
              aria-pressed={isActive}
              disabled={disabled}
            >
              {IconComponent && <IconComponent size={18} strokeWidth={1.8} />}
            </button>
          );
        })}

        <div className={styles.moreWrapper}>
          <button
            type="button"
            className={`${styles.primaryButton} ${styles.moreButton}`}
            onClick={handleToggleMenu}
            aria-haspopup="menu"
            aria-expanded={isMenuOpen}
            disabled={disabled}
            ref={triggerRef}
          >
            <MoreHorizontal size={16} />
          </button>
          {isMenuOpen && isPortalReady && menuCoords &&
            createPortal(
              <div
                className={styles.menuPanel}
                role="menu"
                ref={menuRef}
                style={{ top: menuCoords.top, left: menuCoords.left, width: menuCoords.width }}
              >
                <div className={styles.menuHeader}>{t('books.dialog.coverIconPicker.allIcons')}</div>
                <div className={styles.menuList}>
                  {BOOK_COVER_ICON_CATALOG.map((item) => {
                    const IconComponent = getCoverIconComponent(item.id);
                    const isActive = value === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        className={styles.menuItem}
                        data-active={isActive ? 'true' : undefined}
                        onClick={() => handleMenuSelect(item.id)}
                        role="menuitemradio"
                        aria-checked={isActive}
                        title={item.label}
                        aria-label={item.label}
                      >
                        <span className={styles.menuItemIcon} aria-hidden>
                          {IconComponent && <IconComponent size={20} strokeWidth={1.8} />}
                        </span>
                      </button>
                    );
                  })}
                </div>
                <button type="button" className={styles.clearMenuButton} onClick={handleClear} disabled={disabled || !value}>
                  {t('books.dialog.coverIconPicker.clear')}
                </button>
              </div>,
              document.body,
            )}
        </div>
      </div>
    </div>
  );
};

BookCoverIconPicker.displayName = 'BookCoverIconPicker';
