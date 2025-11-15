// app/(admin)/layout.tsx
// ✅ 后台布局（带 sidebar）

import { Layout } from '@/components/shared';

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Layout showSidebar>
      {children}
    </Layout>
  );
}
