// ============ Application Configuration ============

export const config = {
  // API
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:30001',
    prefix: '/api/v1',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10),
  },

  // Theme
  theme: {
    default: (process.env.NEXT_PUBLIC_DEFAULT_THEME as 'Light' | 'Dark' | 'Loom') || 'Light',
    storageKey: 'wl_theme',
    modeStorageKey: 'wl_mode',
  },

  // Auth
  auth: {
    tokenKey: 'wl_token',
    refreshTokenKey: 'wl_refresh_token',
  },

  // Pagination
  pagination: {
    defaultPageSize: 20,
    maxPageSize: 100,
  },

  // Timeouts
  timeouts: {
    debounce: 300,
    request: 30000,
    staleTime: 5 * 60 * 1000, // 5 minutes
  },
};
