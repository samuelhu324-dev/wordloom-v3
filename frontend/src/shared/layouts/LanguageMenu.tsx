"use client";
import React, { useEffect, useRef, useState } from 'react';
import styles from './LanguageMenu.module.css';
import { useI18n } from '@/i18n/useI18n';
import type { SupportedLanguage } from '@/i18n/config';
import type { MessageKey } from '@/i18n/I18nContext';

type LanguageOption = {
  value: SupportedLanguage;
  labelKey: MessageKey;
};

const LANGUAGE_OPTIONS: LanguageOption[] = [
  { value: 'zh-CN', labelKey: 'language.zhCN' },
  { value: 'en-US', labelKey: 'language.enUS' },
];

export const LanguageMenu: React.FC = () => {
  const [mounted, setMounted] = useState(false);
  const [open, setOpen] = useState(false);
  const hoverTimerRef = useRef<number | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const { t, lang, setLang } = useI18n();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Avoid hydration mismatch when language is resolved from client storage.
  const languageLabel = mounted ? t('nav.language') : 'Language';

  const clearHoverTimer = () => {
    if (hoverTimerRef.current) {
      window.clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  };

  const handleMouseEnter = () => {
    clearHoverTimer();
    hoverTimerRef.current = window.setTimeout(() => setOpen(true), 120);
  };

  const handleMouseLeave = () => {
    clearHoverTimer();
    hoverTimerRef.current = window.setTimeout(() => setOpen(false), 200);
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && open) {
        setOpen(false);
        buttonRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [open]);

  useEffect(() => {
    if (open) {
      const firstButton = menuRef.current?.querySelector('[data-menuitem]') as HTMLElement | null;
      firstButton?.focus();
    }
  }, [open]);

  const handleKeyDown = (event: React.KeyboardEvent) => {
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

  return (
    <div
      className={styles.container}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <button
        ref={buttonRef}
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={languageLabel}
        className={styles.trigger}
        onClick={() => setOpen(o => !o)}
        onKeyDown={handleKeyDown}
      >
        {languageLabel} <span className={styles.caret} aria-hidden="true">▾</span>
      </button>
      {open && (
        <div
          ref={menuRef}
          role="menu"
          aria-label={languageLabel}
          className={styles.panel}
        >
          <div className={styles.activeBar} />
          <ul className={styles.list}>
            {LANGUAGE_OPTIONS.map(option => {
              const active = lang === option.value;
              return (
                <li key={option.value} className={active ? styles.active : undefined}>
                  <button
                    type="button"
                    role="menuitem"
                    tabIndex={-1}
                    data-menuitem
                    aria-pressed={active}
                    className={styles.menuItem}
                    onClick={() => {
                      if (!active) {
                        setLang(option.value);
                      }
                      setOpen(false);
                    }}
                  >
                    {t(option.labelKey)}
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
