
"use client";

import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

type ThemeName = "sky" | "indigo" | "maroon" | "system";
type ThemeCtx = {
  theme: ThemeName;
  setTheme: (t: ThemeName) => void;
};

const ThemeContext = createContext<ThemeCtx | null>(null);

const THEME_KEY_NEW = "wordloom.theme";
const THEME_KEY_OLD = "wl-theme"; // for migration

function readTheme(): ThemeName {
  if (typeof window === "undefined") return "indigo";
  try {
    // migrate old key if present
    const legacy = window.localStorage.getItem(THEME_KEY_OLD);
    if (legacy) {
      window.localStorage.setItem(THEME_KEY_NEW, legacy as string);
      window.localStorage.removeItem(THEME_KEY_OLD);
    }
    const v = (window.localStorage.getItem(THEME_KEY_NEW) || "").trim() as ThemeName;
    if (v === "sky" || v === "indigo" || v === "maroon" || v === "system") return v;
  } catch {}
  return "indigo";
}

function applyTheme(t: ThemeName) {
  const el = typeof document !== "undefined" ? document.documentElement : null;
  if (!el) return;
  const value = t === "system" ? preferredSystemTheme() : t;
  el.setAttribute("data-theme", value);
}

function preferredSystemTheme(): ThemeName {
  if (typeof window === "undefined") return "indigo";
  const dark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  // 这里你有自定义的 dark 主题可接入；目前先沿用 indigo 作为系统默认
  return "indigo";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeName>(readTheme);

  useEffect(() => {
    // 首次挂载时应用一次
    applyTheme(theme);
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(THEME_KEY_NEW, theme);
    } catch {}
    applyTheme(theme);
  }, [theme]);

  const ctx = useMemo<ThemeCtx>(() => ({
    theme,
    setTheme: (t) => setThemeState(t),
  }), [theme]);

  return <ThemeContext.Provider value={ctx}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
