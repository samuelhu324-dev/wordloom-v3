// components/shared/Layout.tsx
// ✅ 全局布局

import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

export interface LayoutProps {
  children?: React.ReactNode;
  showSidebar?: boolean;
}

export function Layout({ children, showSidebar = true }: LayoutProps) {
  return (
    <div className="layout">
      <Header />
      <div className="layout-main">
        {showSidebar && <Sidebar />}
        <main className="layout-content">{children}</main>
      </div>
    </div>
  );
}
