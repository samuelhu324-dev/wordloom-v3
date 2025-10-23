'use client';

import { QueryClientProvider } from '@tanstack/react-query';
import { ReactNode, useMemo } from 'react';
import { getQueryClient } from '@/lib/queryClient';

export default function QueryProvider({ children }: { children: ReactNode }) {
  // 独立拿单例，避免 RSC / CSR 环境冲突
  const client = useMemo(() => getQueryClient(), []);
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
