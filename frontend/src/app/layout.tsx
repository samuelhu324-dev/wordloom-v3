import type { Metadata } from 'next';
import { Providers } from './providers';
import { defaultLanguage } from '@/i18n/config';
import '@/shared/styles/globals.css';

export const metadata: Metadata = {
  title: 'Wordloom',
  description: 'Knowledge Management System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang={defaultLanguage} data-theme="silk-blue">
      <head>
        <link rel="preconnect" href="http://localhost:30001" />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
