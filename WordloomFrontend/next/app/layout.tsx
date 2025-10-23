// src/app/layout.tsx — Batch A (providers path version)
import type { Metadata } from "next";
import "@/styles/globals.css";

import Sidebar from "@/components/common/Sidebar";
import QueryProvider from "@/providers/QueryProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";

export const metadata: Metadata = {
  title: "Wordloom",
  description: "Personal translation + knowledge studio",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <head />
      <body className="min-h-screen bg-[var(--bg)] text-[var(--fg)]">
        <ThemeProvider>
          <QueryProvider>
            <div className="flex">
              <Sidebar />
              <main className="flex-1 min-h-screen">
                <div className="mx-auto max-w-5xl px-6 py-8">{children}</div>
              </main>
            </div>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
