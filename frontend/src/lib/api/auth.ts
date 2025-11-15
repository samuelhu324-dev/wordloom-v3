/**
 * Authentication API Endpoints
 * Handles /auth and related operations
 */

import { apiClient } from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  refresh_token: string;
  user: {
    id: string;
    email: string;
    name?: string;
  };
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  token: string;
}

/**
 * Login with email and password
 */
export async function login(request: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/auth/login', request);
  return response.data;
}

/**
 * Refresh access token
 */
export async function refreshToken(request: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  const response = await apiClient.post<RefreshTokenResponse>('/auth/refresh', request);
  return response.data;
}

/**
 * Logout (optional: notify backend)
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout', {});
  } catch (error) {
    // Ignore logout errors
  }
}

/**
 * Get current user profile
 */
export async function getCurrentUser() {
  const response = await apiClient.get('/auth/me');
  return response.data;
}
