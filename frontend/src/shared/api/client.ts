'use client';

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';

const normalizeBaseOrigin = (input?: string | null): string => {
  if (!input) {
    return '';
  }
  return input.replace(/\/+$/, '');
};

const isBrowser = typeof window !== 'undefined';
const envBaseOrigin = normalizeBaseOrigin(process.env.NEXT_PUBLIC_API_BASE?.trim() || '');
const DEFAULT_SERVER_BASE = 'http://localhost:30001';

// 浏览器侧默认走同源（空字符串），由 Next rewrites → API_PROXY_TARGET 处理跨端口代理；
// 仅在 Storybook/脚本/CI 等脱离 Next 环境时才依赖 NEXT_PUBLIC_API_BASE 或回落到 localhost:30001。
const API_BASE_URL = envBaseOrigin || (isBrowser ? '' : DEFAULT_SERVER_BASE);
const RAW_API_PREFIX = process.env.NEXT_PUBLIC_API_PREFIX || '/api/v1';
const API_PREFIX = RAW_API_PREFIX.startsWith('/') ? RAW_API_PREFIX : `/${RAW_API_PREFIX}`;

export const API_BASE_ORIGIN = API_BASE_URL;
export const API_PREFIX_PATH = API_PREFIX;
export const API_ROOT = `${API_BASE_ORIGIN}${API_PREFIX_PATH}`;

export const buildApiUrl = (path: string): string => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_ROOT}${normalizedPath}`;
};

// ============ API 客户端配置 ============
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_ROOT,
  timeout: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10),
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============ 请求拦截器 ============
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 添加 JWT Token
    const token = typeof window !== 'undefined' ? localStorage.getItem('wl_token') : null;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // 开发期前缀 & URL 使用规范守卫 (RULE_API_PREFIX_001)
    if (process.env.NODE_ENV !== 'production') {
      const rawUrl = config.url || '';

      // 1. 禁止传入绝对 URL（应只写资源相对路径）
      if (/^https?:\/\//i.test(rawUrl)) {
        // 保留仍可请求，但提示重构。
        console.warn('[api prefix guard] 传入绝对 URL: ' + rawUrl + '。请改为相对资源路径 (例如 /libraries)。');
      }

      // 2. 防止重复包含 /api/v1 前缀（baseURL 已含前缀）
      if (rawUrl.startsWith('/api/v1/')) {
        console.warn('[api prefix guard] 路径包含重复前缀 /api/v1，将自动剥离。原始: ' + rawUrl);
        config.url = rawUrl.replace(/^\/api\/v1\//, '/');
      }

      // 3. 确保以 '/' 开头（否则 axios 会拼接为奇怪的相对路径）
      if (config.url && !config.url.startsWith('/')) {
        console.warn('[api prefix guard] 路径未以 / 开头: ' + config.url + '。自动补全。');
        config.url = '/' + config.url;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============ 响应拦截器 ============
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    // 处理全局错误
    if (error.response?.status === 401) {
      // Token 过期，清理并重定向到登录
      if (typeof window !== 'undefined') {
        localStorage.removeItem('wl_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ============ HTTP 方法封装 ============
export const api = {
  get<T = any>(url: string, config?: AxiosRequestConfig) {
    return apiClient.get<T>(url, config);
  },
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return apiClient.post<T>(url, data, config);
  },
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return apiClient.patch<T>(url, data, config);
  },
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
    return apiClient.put<T>(url, data, config);
  },
  delete<T = any>(url: string, config?: AxiosRequestConfig) {
    return apiClient.delete<T>(url, config);
  },
};

export default apiClient;
