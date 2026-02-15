import type { Metadata } from 'next';
import { Providers } from './providers';
import { defaultLanguage } from '@/i18n/config';
import '@/shared/styles/globals.css';

export const metadata: Metadata = {
  title: 'Wordloom',
  description: 'Knowledge Management System',
};

const normalizeOrigin = (value: string): string => value.replace(/\/+$/, '');
const apiOrigin = normalizeOrigin(
  process.env.API_PROXY_TARGET || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:30001'
);

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={defaultLanguage} data-theme="silk-blue">
      <head>
        <link rel="preconnect" href={apiOrigin} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
