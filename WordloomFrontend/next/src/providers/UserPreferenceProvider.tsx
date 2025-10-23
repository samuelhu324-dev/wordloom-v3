"use client";

import React, { createContext, useCallback, useContext, useEffect, useState } from "react";

export type Prefs = {
  fontFamily: "sans" | "serif";
  baseSize: number;
  lineHeight: number;
  letterSpacing: number;
};

type PrefsCtx = {
  prefs: Prefs;
  update: (patch: Partial<Prefs>) => void;
  reset: () => void;
};

const DEFAULT_PREFS: Prefs = {
  fontFamily: "serif",
  baseSize: 16,
  lineHeight: 1.7,
  letterSpacing: 0,
};

const STORAGE_KEY_PREFS = "wl_prefs";
const PrefsContext = createContext<PrefsCtx | null>(null);

export function UserPreferenceProvider({ children }: { children: React.ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>(() => {
    if (typeof window === "undefined") return DEFAULT_PREFS;
    try {
      const raw = localStorage.getItem(STORAGE_KEY_PREFS);
      return raw ? { ...DEFAULT_PREFS, ...JSON.parse(raw) } : DEFAULT_PREFS;
    } catch { return DEFAULT_PREFS; }
  });

  const applyToDom = useCallback((p: Prefs) => {
    if (typeof document === "undefined") return;
    const r = document.documentElement;
    r.style.setProperty("--font-family", p.fontFamily === "serif" ? "var(--font-serif)" : "var(--font-sans)");
    r.style.setProperty("--font-size-base", `${p.baseSize}px`);
    r.style.setProperty("--line-height", String(p.lineHeight));
    r.style.setProperty("--letter-spacing", `${p.letterSpacing}em`);
  }, []);

  useEffect(() => { applyToDom(prefs); }, []);
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_PREFS, JSON.stringify(prefs));
    applyToDom(prefs);
  }, [prefs, applyToDom]);

  const update = useCallback((patch: Partial<Prefs>) => setPrefs(prev => ({ ...prev, ...patch })), []);
  const reset = useCallback(() => setPrefs(DEFAULT_PREFS), []);

  return (
    <PrefsContext.Provider value={{ prefs, update, reset }}>
      {children}
    </PrefsContext.Provider>
  );
}

export function useUserPrefs() {
  const ctx = useContext(PrefsContext);
  if (!ctx) throw new Error("useUserPrefs must be used within UserPreferenceProvider");
  return ctx;
}
