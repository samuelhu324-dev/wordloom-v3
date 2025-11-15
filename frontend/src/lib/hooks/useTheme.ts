/**
 * useTheme Hook
 * Provides theme and mode switching with localStorage persistence
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { ThemeName, ThemeMode, getAvailableThemes } from '../themes';

interface UseThemeReturn {
  currentTheme: ThemeName;
  currentMode: ThemeMode;
  availableThemes: ThemeName[];
  setTheme: (theme: ThemeName) => void;
  setMode: (mode: ThemeMode) => void;
}

const THEME_STORAGE_KEY = 'wl_theme';
const MODE_STORAGE_KEY = 'wl_mode';

export function useTheme(defaultTheme: ThemeName = 'Light'): UseThemeReturn {
  const [currentTheme, setCurrentTheme] = useState<ThemeName>(defaultTheme);
  const [currentMode, setCurrentMode] = useState<ThemeMode>('light');
  const [isHydrated, setIsHydrated] = useState(false);

  // Load from localStorage on mount
  useEffect(() => {
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) as ThemeName | null;
    const savedMode = localStorage.getItem(MODE_STORAGE_KEY) as ThemeMode | null;

    if (savedTheme && getAvailableThemes().includes(savedTheme)) {
      setCurrentTheme(savedTheme);
    }

    if (savedMode) {
      setCurrentMode(savedMode);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setCurrentMode(prefersDark ? 'dark' : 'light');
    }

    setIsHydrated(true);
  }, []);

  const handleSetTheme = useCallback((theme: ThemeName) => {
    setCurrentTheme(theme);
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  }, []);

  const handleSetMode = useCallback((mode: ThemeMode) => {
    setCurrentMode(mode);
    localStorage.setItem(MODE_STORAGE_KEY, mode);
  }, []);

  return {
    currentTheme: isHydrated ? currentTheme : defaultTheme,
    currentMode: isHydrated ? currentMode : 'light',
    availableThemes: getAvailableThemes(),
    setTheme: handleSetTheme,
    setMode: handleSetMode,
  };
}
