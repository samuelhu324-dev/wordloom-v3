import type { Metadata } from 'next';
import { Providers } from './providers';
import '@/shared/styles/globals.css';

export const metadata: Metadata = {
  title: 'Wordloom',
  description: 'Knowledge Management System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="Light">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
