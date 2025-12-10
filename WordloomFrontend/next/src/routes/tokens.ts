export const APP = {
  LOOM: "app.loom",
  LOOM_CREATION: "app.loom.creation",
  LOOM_MANAGEMENT: "app.loom.management",
} as const;

export const API = {
  ENTRIES: {
    SEARCH: "api.entries.search",
    BY_ID: "api.entries.by_id",
    BULK_REPLACE: "api.entries.bulk_replace",
    BATCH: "api.entries.batch",
    RECENT: "api.entries.recent",
  },
  SOURCES: {
    LIST: "api.sources.list",
    RENAME: "api.sources.rename",
  },
  AUTH: { LOGIN: "api.auth.login" },
} as const;

export type AppToken = typeof APP[keyof typeof APP];
export type ApiToken =
  | typeof API.ENTRIES[keyof typeof API.ENTRIES]
  | typeof API.SOURCES[keyof typeof API.SOURCES]
  | typeof API.AUTH[keyof typeof API.AUTH];
