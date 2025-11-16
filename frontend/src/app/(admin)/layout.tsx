import type { Metadata } from 'next';
import { Layout } from '@/shared/layouts';

export const metadata: Metadata = {
  title: 'Admin - Wordloom',
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <Layout showSidebar>{children}</Layout>;
}
