'use client';

import React from 'react';
import styles from './LanguageSwitcher.module.css';
import { useI18n } from './useI18n';
import type { SupportedLanguage } from './config';
import type { MessageKey } from './I18nContext';

type LanguageOption = {
  value: SupportedLanguage;
  labelKey: MessageKey;
};

const OPTIONS: LanguageOption[] = [
  { value: 'zh-CN', labelKey: 'language.zhCN' },
  { value: 'en-US', labelKey: 'language.enUS' },
];

type LanguageSwitcherProps = {
  variant?: 'inline' | 'menu';
  onSelect?: () => void;
};

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ variant = 'inline', onSelect }) => {
  const { lang, setLang, t } = useI18n();

  return (
    <div
      className={
        variant === 'menu'
          ? `${styles.switcher} ${styles.switcherMenu}`
          : styles.switcher
      }
    >
      {OPTIONS.map(option => {
        const active = lang === option.value;
        const buttonClassName = [
          styles.button,
          variant === 'menu' ? styles.menuButton : styles.inlineButton,
          active ? (variant === 'menu' ? styles.activeMenu : styles.activeInline) : '',
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => {
              if (!active) {
                setLang(option.value);
              }
              onSelect?.();
            }}
            className={buttonClassName}
          >
            {t(option.labelKey)}
          </button>
        );
      })}
    </div>
  );
};
