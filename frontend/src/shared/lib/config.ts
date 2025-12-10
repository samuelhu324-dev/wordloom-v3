import type { Theme } from '../providers/ThemeProvider';
// ============ Application Configuration ============

export const config = {
  // API
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:30001',
    prefix: process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1',
    timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10),
  },

  // Feature Flags
  flags: {
    // 启用/禁用模拟数据模式
    // ✅ Nov 17, 2025: 后端async Repository完成 + Windows兼容性修复
    // 现在useMock = false可以安全地连接真实后端API
    useMock:
      (process.env.NEXT_PUBLIC_USE_MOCK || '').toLowerCase() === '1' ||
      (process.env.NEXT_PUBLIC_USE_MOCK || '').toLowerCase() === 'true',
  },

  // Theme
  theme: {
    default: (process.env.NEXT_PUBLIC_DEFAULT_THEME as Theme) || 'silk-blue',
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
