// app/layout.tsx
import type { Metadata } from 'next';
import '@/styles/globals.css';
import QueryProvider from '@/providers/QueryProvider';
import { ThemeProvider } from '@/providers/ThemeProvider';
import Sidebar from '@/components/common/Sidebar';

export const metadata: Metadata = {
  title: 'Wordloom',
  description: 'Wordloom Frontend',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        {/* 仍使用 Sidebar 作为主菜单 */}
        <QueryProvider>
          <ThemeProvider>
            <Sidebar />
            {/* 改用 app-main + 内层居中容器 */}
            <main className="app-main">
              <div className="page-container">
                {children}
              </div>
            </main>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
