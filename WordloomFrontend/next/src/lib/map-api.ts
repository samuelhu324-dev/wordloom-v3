// src/lib/map-api.ts — unified API path helpers
// 统一 API 常量，避免硬编码路径重复

export const API = {
  ENTRIES: "/entries",
  SOURCES: "/sources",
} as const;

export const API_ORBIT = {
  BASE: '/api/orbit',
  MEMOS: '/api/orbit/memos',
  TASKS: '/api/orbit/tasks',
  STATS: '/api/orbit/stats',
  UPLOADS: '/api/orbit/uploads',
} as const;

/**
 * 拼接 API 路径（不含基址，由 apiFetch 负责补全）
 * @example api(API.ENTRIES) => "/entries"
 */
export const api = (p: string) => p;

/**
 * 拼接 Orbit API 路径
 * @example apiOrbit(API_ORBIT.MEMOS) => "/orbit/memos"
 */
export const apiOrbit = (p: string) => {
  return p.startsWith('/api/orbit') ? p : `${API_ORBIT.BASE}${p}`;
};

export { API_BASE, resolveApiUrl, apiFetch } from './api';
