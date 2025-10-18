import type { Metadata } from "next";
import "../src/styles/globals.css";
import "../src/styles/tokens.css";
import Sidebar from "../src/components/common/Sidebar";
import QueryProvider from "../src/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "Wordloom",
  description: "Wordloom Frontend",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-white text-gray-900">
        <QueryProvider>
          <div className="flex">
            <Sidebar />
            <main className="flex-1 min-h-screen">
              {/* 顶部留出统一的页内边距，避免你说的“一打开就是一堆内容”压到边上 */}
              <div className="mx-auto max-w-5xl px-6 py-8">
                {children}
              </div>
            </main>
          </div>
        </QueryProvider>
      </body>
    </html>
  );
}
