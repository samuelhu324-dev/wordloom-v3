'use client';

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:30001';
const API_PREFIX = '/api/v1';

// ============ API 客户端配置 ============
export const apiClient: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
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
