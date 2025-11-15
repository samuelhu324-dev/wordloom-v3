/**
 * useAuth Hook
 * Provides authentication state and operations
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { logout } from '../api/auth';

interface User {
  id: string;
  email: string;
  name?: string;
}

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => Promise<void>;
}

export function useAuth(): UseAuthReturn {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check token on mount
  useEffect(() => {
    const token = localStorage.getItem('wl_token');
    if (token) {
      // In real app, validate token with backend
      // For now, assume valid
      setUser({
        id: '1',
        email: 'user@example.com',
      });
    }
    setIsLoading(false);
  }, []);

  const handleLogout = useCallback(async () => {
    await logout();
    localStorage.removeItem('wl_token');
    localStorage.removeItem('wl_refresh_token');
    setUser(null);
    window.location.href = '/auth/login';
  }, []);

  return {
    user,
    isAuthenticated: !!user,
    isLoading,
    logout: handleLogout,
  };
}
