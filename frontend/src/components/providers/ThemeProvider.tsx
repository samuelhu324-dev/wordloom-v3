/**
 * ThemeProvider
 * Dynamically injects CSS Variables at runtime
 * Supports hydration to prevent SSR flicker
 */

'use client';

import React, { createContext, useContext, ReactNode, useEffect } from 'react';
import { useTheme } from '@/lib/hooks';
import { themes, generateCSSVariables, ThemeName, ThemeMode } from '@/lib/themes';
import { config } from '@/lib/config';

interface ThemeContextType {
  currentTheme: ThemeName;
  currentMode: ThemeMode;
  availableThemes: ThemeName[];
  setTheme: (theme: ThemeName) => void;
  setMode: (mode: ThemeMode) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const themeState = useTheme(config.theme.default);

  // Inject CSS Variables on theme/mode change
  useEffect(() => {
    const colors = themes[themeState.currentTheme][themeState.currentMode];
    const cssVariables = generateCSSVariables(colors);

    // Create or update style tag
    let styleTag = document.getElementById('wl-theme-styles');
    if (!styleTag) {
      styleTag = document.createElement('style');
      styleTag.id = 'wl-theme-styles';
      document.head.appendChild(styleTag);
    }
    styleTag.textContent = `:root { ${cssVariables} }`;

    // Set data-theme attribute for CSS selectors (optional)
    document.documentElement.setAttribute('data-theme', themeState.currentTheme);
    document.documentElement.setAttribute('data-mode', themeState.currentMode);
  }, [themeState.currentTheme, themeState.currentMode]);

  return (
    <ThemeContext.Provider value={themeState}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useThemeContext must be used within ThemeProvider');
  }
  return context;
}
