/**
 * Routing map for API endpoints.
 * Keep these as FRONTEND virtual paths; Next.js rewrites to /api/common/*
 */
export const API = {
  LOOM_ENTRIES: "/loom/entries",
  LOOM_SOURCES: "/loom/sources",
} as const;

/** Compatibility shim: some components import this; keep it as identity mapper. */
export const resolveApiPath = (p: string) => p;
