// src/components/common/SidebarToggle.tsx
'use client';

import { useEffect, useState } from 'react';

const KEY = 'sidebar-open'; // localStorage 持久化

export default function SidebarToggle() {
  const [open, setOpen] = useState<boolean>(false);

  // 初始化：从 localStorage 恢复，并写入 <html data-sidebar-state>
  useEffect(() => {
    try {
      const saved = localStorage.getItem(KEY);
      const init = saved === '1';
      setOpen(init);
      document.documentElement.setAttribute('data-sidebar-state', init ? 'open' : 'closed');
    } catch {
      document.documentElement.setAttribute('data-sidebar-state', 'closed');
    }
  }, []);

  // 切换：更新 dataset + 持久化
  const toggle = () => {
    const next = !open;
    setOpen(next);
    document.documentElement.setAttribute('data-sidebar-state', next ? 'open' : 'closed');
    try { localStorage.setItem(KEY, next ? '1' : '0'); } catch {}
  };

  return (
    <button
      className="sidebar-toggle"
      onClick={toggle}
      aria-expanded={open}
      aria-label="Toggle sidebar"
      type="button"
    >
      {open ? '«' : '»'}
    </button>
  );
}
