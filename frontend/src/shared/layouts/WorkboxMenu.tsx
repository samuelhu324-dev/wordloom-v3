"use client";
import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import styles from './WorkboxMenu.module.css';

type MenuItem = {
  href: string;
  key: string;
  labelKey: MessageKey;
};

const MENU_ITEMS: MenuItem[] = [
  { href: '/admin/libraries', labelKey: 'nav.libraries', key: 'libraries' },
  { href: '/admin/basement', labelKey: 'nav.basement', key: 'basement' },
  { href: '/admin/chronicle', labelKey: 'nav.chronicle', key: 'chronicle' },
  { href: '/admin/tags', labelKey: 'nav.tags', key: 'tags' },
];

export const WorkboxMenu: React.FC = () => {
  const [open, setOpen] = useState(false);
  const hoverTimerRef = useRef<number | null>(null);
  const pathname = usePathname();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const { t } = useI18n();

  // Hover logic with delays
  const handleMouseEnter = () => {
    if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = window.setTimeout(() => setOpen(true), 120);
  };

  const handleMouseLeave = () => {
    if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = window.setTimeout(() => setOpen(false), 200);
  };

  // Keyboard: Esc to close
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  // Focus first item when opening via keyboard
  useEffect(() => {
    if (open) {
      const firstItem = menuRef.current?.querySelector('[data-menuitem]') as HTMLElement | null;
      firstItem?.focus();
    }
  }, [open]);

  // Arrow navigation inside menu
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!open) return;
    const items = Array.from(menuRef.current?.querySelectorAll('[data-menuitem]') || []) as HTMLElement[];
    const currentIndex = items.indexOf(document.activeElement as HTMLElement);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIndex = (currentIndex + 1) % items.length;
      items[nextIndex]?.focus();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      items[prevIndex]?.focus();
    }
  };

  return (
    <div
      className={styles.container}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="true"
        aria-expanded={open}
        aria-label={t('nav.workbox')}
        className={styles.trigger}
        onClick={() => setOpen(o => !o)}
        onKeyDown={handleKeyDown}
      >
        {t('nav.workbox')} <span className={styles.caret} aria-hidden="true">▾</span>
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-label={t('nav.workbox')}
          className={styles.panel}
        >
          <div className={styles.activeBar} />
          <ul className={styles.list}>
            {MENU_ITEMS.map(item => {
              const active = pathname?.startsWith(item.href);
              return (
                <li key={item.key} className={active ? styles.active : undefined}>
                  <Link
                    href={item.href}
                    role="menuitem"
                    tabIndex={-1}
                    data-menuitem
                    onClick={() => setOpen(false)}
                    className={styles.menuItem}
                  >
                    {t(item.labelKey)}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};
