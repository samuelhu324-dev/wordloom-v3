// components/shared/Header.tsx
// ✅ 顶部栏

'use client';

import React from 'react';
import { ThemeSwitcher } from './ThemeSwitcher';

export function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-logo">
          <h1>Wordloom</h1>
        </div>
        <nav className="header-nav">
          <ThemeSwitcher />
        </nav>
      </div>
    </header>
  );
}
