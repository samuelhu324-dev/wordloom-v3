import { ReactNode, Suspense } from 'react';
import { Header } from '@/shared/layouts';

interface AdminLayoutProps {
  children: ReactNode;
}

export const dynamic = 'force-dynamic';

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Suspense fallback={<div style={{ minHeight: 64 }} />}>
        <Header />
      </Suspense>
      <div style={{ flex: 1 }}>
        {children}
      </div>
    </div>
  );
}
