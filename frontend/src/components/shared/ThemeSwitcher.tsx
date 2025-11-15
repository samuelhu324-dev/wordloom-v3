// components/shared/ThemeSwitcher.tsx
// ✅ 主题/模式切换 UI

'use client';

import React from 'react';
import { useTheme } from '@/lib/hooks/useTheme';
import { THEMES } from '@/lib/themes';
import { Moon, Sun } from 'lucide-react';

export function ThemeSwitcher() {
  const { currentTheme, currentMode, availableThemes, setTheme, setMode } = useTheme();

  return (
    <div className="theme-switcher">
      <select
        value={currentTheme}
        onChange={(e) => setTheme(e.target.value as any)}
        className="theme-select"
      >
        {availableThemes.map((theme) => (
          <option key={theme} value={theme}>
            {THEMES[theme].name}
          </option>
        ))}
      </select>

      <button
        onClick={() => setMode(currentMode === 'light' ? 'dark' : 'light')}
        className="mode-toggle"
        aria-label={`Switch to ${currentMode === 'light' ? 'dark' : 'light'} mode`}
      >
        {currentMode === 'light' ? (
          <Moon size={18} />
        ) : (
          <Sun size={18} />
        )}
      </button>
    </div>
  );
}
