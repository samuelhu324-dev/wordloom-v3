// components/shared/Sidebar.tsx
// ✅ 侧边栏

'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <aside className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
      <button
        className="sidebar-toggle"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle sidebar"
      >
        ☰
      </button>

      {isOpen && (
        <nav className="sidebar-nav">
          <Link href="/admin/dashboard">Dashboard</Link>
        </nav>
      )}
    </aside>
  );
}
