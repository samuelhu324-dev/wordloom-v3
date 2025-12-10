'use client';

import React, { createContext, useContext, useEffect } from 'react';

export type Theme =
  | 'business-blue'
  | 'silk-blue'
  | 'light'
  | 'dark'
  | 'loom'
  | 'loom-dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const STORAGE_KEY = 'wl_theme';
const DEFAULT_THEME: Theme = 'silk-blue';

const legacyThemeMappings: Record<string, Theme> = {
  Light: 'silk-blue',
  Dark: 'dark',
  Loom: 'loom',
  'Loom-Dark': 'loom-dark',
};

const applyThemeToDocument = (nextTheme: Theme) => {
  document.documentElement.setAttribute('data-theme', nextTheme);
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = React.useState<Theme>(DEFAULT_THEME);

  useEffect(() => {
    const storedRaw = localStorage.getItem(STORAGE_KEY);
    const normalized = storedRaw
      ? (legacyThemeMappings[storedRaw] ?? (storedRaw as Theme))
      : null;

    const initialTheme = normalized ?? DEFAULT_THEME;
    setThemeState(initialTheme);
    applyThemeToDocument(initialTheme);
  }, []);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem(STORAGE_KEY, newTheme);
    applyThemeToDocument(newTheme);
  };

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
