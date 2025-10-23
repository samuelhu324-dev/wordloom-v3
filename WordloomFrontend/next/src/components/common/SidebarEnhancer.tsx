"use client";

import React, { useState } from "react";
import { useSwipeCollapse } from "./useSwipeCollapse";

/** 包一层给 Sidebar 提供过渡与手势（不改你现有 Sidebar 逻辑） */
export default function SidebarEnhancer({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  const swipe = useSwipeCollapse({
    axis: "x",
    threshold: 50,
    onCollapse: () => setOpen(false),
    onExpand: () => setOpen(true),
  });

  return (
    <aside
      {...swipe}
      className="transition-all duration-200 ease-in-out"
      style={{
        width: open ? 260 : 0,
        overflow: "hidden",
        borderRight: open ? "1px solid var(--border)" : "none",
        background: "var(--surface)",
      }}
    >
      {children}
    </aside>
  );
}
