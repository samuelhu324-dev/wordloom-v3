'use client';

import React, { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import { defaultLanguage, isSupportedLanguage, STORAGE_KEY, type SupportedLanguage } from './config';
import { enUS } from './locales/en-US';
import { zhCN } from './locales/zh-CN';

const dictionaries = {
  'zh-CN': zhCN,
  'en-US': enUS,
} as const;

type Messages = typeof enUS;
export type MessageKey = keyof Messages;

type I18nContextValue = {
  lang: SupportedLanguage;
  messages: Messages;
  t: (key: MessageKey, vars?: Record<string, string | number>) => string;
  setLang: (lang: SupportedLanguage) => void;
};

export const I18nContext = createContext<I18nContextValue | null>(null);

export const formatMessage = (template: string, vars?: Record<string, string | number>) => {
  if (!vars) return template;
  return Object.entries(vars).reduce<string>((acc, [token, value]) => {
    return acc.replace(new RegExp(`{${token}}`, 'g'), String(value));
  }, template);
};

const getStoredLanguage = (): SupportedLanguage | null => {
  if (typeof window === 'undefined') return null;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (stored && isSupportedLanguage(stored)) {
    return stored;
  }
  return null;
};

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLangState] = useState<SupportedLanguage>(defaultLanguage);

  useEffect(() => {
    const stored = getStoredLanguage();
    if (stored) {
      setLangState(stored);
    }
  }, []);

  const setLang = useCallback((next: SupportedLanguage) => {
    setLangState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, next);
      // TODO: 将语言同步到 /me/settings 接口
    }
  }, []);

  const messages = dictionaries[lang] ?? dictionaries[defaultLanguage];

  const value = useMemo<I18nContextValue>(() => ({
    lang,
    messages,
    setLang,
    t: (key, vars) => {
      const template = messages[key] ?? key;
      return formatMessage(template, vars);
    },
  }), [lang, messages, setLang]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};
