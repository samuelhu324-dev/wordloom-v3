
// src/lib/prefs.ts
// Export/import appearance preferences (theme + optional font/size) for share links or backups.

export type Appearance = {
  theme?: "sky" | "indigo" | "maroon" | "system";
  font?: string;
  size?: number; // base font size in px
};

const KEY_THEME = "wordloom.theme";
const KEY_FONT  = "wordloom.font";
const KEY_SIZE  = "wordloom.size";

export function exportAppearance(): Appearance {
  if (typeof window === "undefined") return {};
  const theme = (localStorage.getItem(KEY_THEME) || "") as Appearance["theme"];
  const font  = localStorage.getItem(KEY_FONT) || undefined;
  const sizeStr = localStorage.getItem(KEY_SIZE) || "";
  const size = sizeStr ? Number(sizeStr) : undefined;
  const apx: Appearance = {};
  if (theme) apx.theme = theme;
  if (font)  apx.font  = font;
  if (size && !Number.isNaN(size)) apx.size = size;
  return apx;
}

export function importAppearance(apx: Appearance) {
  if (typeof window === "undefined" || !apx) return;
  if (apx.theme) localStorage.setItem(KEY_THEME, apx.theme);
  if (apx.font)  localStorage.setItem(KEY_FONT, apx.font);
  if (typeof apx.size === "number" && !Number.isNaN(apx.size)) {
    localStorage.setItem(KEY_SIZE, String(apx.size));
  }
}

// Helpers for URL encoding/decoding (optional)
export function encodeAppearanceToQuery(apx: Appearance): string {
  const u = new URLSearchParams();
  if (apx.theme) u.set("theme", apx.theme);
  if (apx.font)  u.set("font", apx.font);
  if (typeof apx.size === "number") u.set("size", String(apx.size));
  return u.toString();
}

export function decodeAppearanceFromQuery(qs: string): Appearance {
  const u = new URLSearchParams(qs);
  const apx: Appearance = {};
  const t = u.get("theme") as Appearance["theme"] | null;
  if (t) apx.theme = t;
  const f = u.get("font");
  if (f) apx.font = f;
  const s = u.get("size");
  if (s) {
    const n = Number(s);
    if (!Number.isNaN(n)) apx.size = n;
  }
  return apx;
}
