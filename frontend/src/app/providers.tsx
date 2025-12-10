'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/shared/providers';
import { I18nProvider } from '@/i18n/I18nContext';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // Align with hooks, avoid immediate refetch
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </ThemeProvider>
    </I18nProvider>
  );
}
