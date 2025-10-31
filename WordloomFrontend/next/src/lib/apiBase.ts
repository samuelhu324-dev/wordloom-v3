"use client";

// 变量定义要在最前面
const isDev = process.env.NODE_ENV === "development";
const forceAbsolute = process.env.NEXT_PUBLIC_FORCE_ABSOLUTE_API === "1";

// 然后才导入和使用
import { API_BASE, resolveApiUrl, apiFetch } from './api';
export { API_BASE, resolveApiUrl, apiFetch };

// 后端挂载前缀（建议保持相对路径，最终由 apiFetch 用 API_BASE 拼接）
export const ORBIT_BASE = forceAbsolute
  ? (process.env.NEXT_PUBLIC_ORBIT_API_BASE || "http://localhost:8011")
  : "/api/orbit";

export const LOOM_BASE = forceAbsolute
  ? (process.env.NEXT_PUBLIC_LOOM_API_BASE || "http://localhost:8013")
  : "/api/loom";

export const ORBIT_UPLOADS = `${ORBIT_BASE}/uploads`;

// 静态资产前缀（用于把相对路径拼成可访问 URL）
export const ORBIT_ASSET_PREFIX =
  process.env.NEXT_PUBLIC_ORBIT_ASSET_PREFIX ?? '/orbit-assets';

// 向后兼容别名
export const ORBIT_API_BASE = ORBIT_BASE;
