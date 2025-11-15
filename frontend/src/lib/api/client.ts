/**
 * Axios API Client with JWT Interceptors
 * Handles authentication, token refresh, and error mapping
 */

import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { config } from '../config';

interface ApiErrorResponse {
  statusCode: number;
  message: string;
  error?: string;
}

class ApiClient {
  client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: config.api.baseUrl,
      timeout: config.api.timeout,
    });

    this.setupRequestInterceptor();
    this.setupResponseInterceptor();
  }

  private setupRequestInterceptor() {
    this.client.interceptors.request.use(
      (requestConfig) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('wl_token') : null;
        if (token && requestConfig.headers) {
          requestConfig.headers.Authorization = `Bearer ${token}`;
        }
        return requestConfig;
      },
      (error) => Promise.reject(error)
    );
  }

  private setupResponseInterceptor() {
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiErrorResponse>) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('wl_refresh_token') : null;
          if (refreshToken) {
            try {
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken,
              });
              const { token: newToken } = response.data;
              localStorage.setItem('wl_token', newToken);
              // Retry original request
              error.config!.headers.Authorization = `Bearer ${newToken}`;
              return this.client(error.config!);
            } catch (refreshError) {
              // Refresh failed, logout
              if (typeof window !== 'undefined') {
                localStorage.removeItem('wl_token');
                localStorage.removeItem('wl_refresh_token');
                window.location.href = '/auth/login';
              }
            }
          }
        }
        return Promise.reject(error);
      }
    );
  }

  get<T>(url: string, config?: any) {
    return this.client.get<T>(url, config);
  }

  post<T>(url: string, data?: any, config?: any) {
    return this.client.post<T>(url, data, config);
  }

  put<T>(url: string, data?: any, config?: any) {
    return this.client.put<T>(url, data, config);
  }

  patch<T>(url: string, data?: any, config?: any) {
    return this.client.patch<T>(url, data, config);
  }

  delete<T>(url: string, config?: any) {
    return this.client.delete<T>(url, config);
  }
}

export const apiClient = new ApiClient();
