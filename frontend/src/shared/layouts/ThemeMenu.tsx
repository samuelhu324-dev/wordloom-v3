"use client";
import React, { useState, useRef, useEffect } from 'react';
import styles from './ThemeMenu.module.css';
import { useTheme, Theme } from '../providers/ThemeProvider';
import { useI18n } from '@/i18n/useI18n';

interface ThemeOption {
  value: Theme;
  label: string;
  description: string;
}

const THEME_OPTIONS: ThemeOption[] = [
  {
    value: 'silk-blue',
    label: '丝绸蓝',
    description: '黑白主调 + 丝绸蓝点睛 (默认)',
  },
  {
    value: 'business-blue',
    label: '商务蓝',
    description: '旧版商务蓝白配色',
  },
];

export const ThemeMenu: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const { t } = useI18n();
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const hoverTimerRef = useRef<number | null>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Avoid hydration mismatch when language is resolved from client storage.
  const themeLabel = mounted ? t('nav.theme') : 'Theme';

  const handleMouseEnter = () => {
    if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = window.setTimeout(() => setOpen(true), 120);
  };

  const handleMouseLeave = () => {
    if (hoverTimerRef.current) window.clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = window.setTimeout(() => setOpen(false), 200);
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  useEffect(() => {
    if (open) {
      const firstItem = menuRef.current?.querySelector('[data-menuitem]') as HTMLElement | null;
      firstItem?.focus();
    }
  }, [open]);

  const handleMenuKeyDown = (event: React.KeyboardEvent) => {
    if (!open) return;
    const items = Array.from(menuRef.current?.querySelectorAll('[data-menuitem]') || []) as HTMLElement[];
    const currentIndex = items.indexOf(document.activeElement as HTMLElement);

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      const nextIndex = (currentIndex + 1) % items.length;
      items[nextIndex]?.focus();
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIndex = (currentIndex - 1 + items.length) % items.length;
      items[prevIndex]?.focus();
    }
  };

  const handleSelect = (value: Theme) => {
    setTheme(value);
    setOpen(false);
    triggerRef.current?.focus();
  };

  return (
    <div
      className={styles.container}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        ref={triggerRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={themeLabel}
        className={styles.trigger}
        onClick={() => setOpen(prev => !prev)}
        onKeyDown={handleMenuKeyDown}
      >
        {themeLabel} <span className={styles.caret} aria-hidden="true">▾</span>
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-label={themeLabel}
          className={styles.panel}
        >
          <div className={styles.heading}>选择主题</div>
          <ul className={styles.list}>
            {THEME_OPTIONS.map(option => {
              const isActive = theme === option.value;
              return (
                <li key={option.value}>
                  <button
                    type="button"
                    role="menuitemradio"
                    aria-checked={isActive}
                    data-menuitem
                    tabIndex={-1}
                    className={styles.menuItem}
                    onClick={() => handleSelect(option.value)}
                    onKeyDown={handleMenuKeyDown}
                  >
                    <span className={styles.indicator}>{isActive ? '●' : ''}</span>
                    <span className={styles.label}>
                      <span>{option.label}</span>
                      <span>{option.description}</span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
};
