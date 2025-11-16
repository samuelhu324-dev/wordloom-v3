// app/layout.tsx
// ✅ 根布局 - 组装所有 providers

import type { Metadata } from 'next';
import '@/styles/tokens.css';
import '@/styles/globals.css';
import '@/styles/button.css';
import '@/styles/card.css';
import '@/styles/input.css';
import '@/styles/util-surface.css';
import '@/styles/modal.css';
import '@/styles/skeleton.css';
import '@/styles/toast.css';
import { AuthProvider, ThemeProvider, QueryProvider } from '@/components/providers';

export const metadata: Metadata = {
  title: 'Wordloom',
  description: 'Your personal knowledge management system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta charSet="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body>
        <ThemeProvider>
          <AuthProvider>
            <QueryProvider>
              {children}
            </QueryProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
