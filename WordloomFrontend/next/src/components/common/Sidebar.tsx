"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

function cx(...cls: (string | false | undefined)[]) {
  return cls.filter(Boolean).join(" ");
}

const items = [
  { href: "/",      label: "Home",       emoji: "🏠" },
  { href: "/admin", label: "Home Admin", emoji: "🛠️" },
  { href: "/from",  label: "From Page",  emoji: "📑" },
  { href: "/insert",label: "Insert",     emoji: "📚" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  // 记忆折叠状态（刷新/重开页面仍生效）
  useEffect(() => {
    const v = localStorage.getItem("wl_sidebar_collapsed");
    if (v === "1") setCollapsed(true);
  }, []);
  useEffect(() => {
    localStorage.setItem("wl_sidebar_collapsed", collapsed ? "1" : "0");
  }, [collapsed]);

  return (
    <aside
      className={cx(
        "h-screen border-r bg-white/60 backdrop-blur-sm sticky top-0 transition-all",
        collapsed ? "w-16" : "w-56"
      )}
    >
      <div className={cx("flex items-center justify-between px-3 py-3")}>
        <div className={cx("text-sm text-gray-500", collapsed && "sr-only")}>Home</div>
        <button
          aria-label={collapsed ? "展开侧边栏" : "收起侧边栏"}
          className="ml-auto rounded-md border px-2 py-1 text-xs text-gray-600 hover:bg-gray-50"
          onClick={() => setCollapsed(v => !v)}
          title={collapsed ? "展开" : "收起"}
        >
          {collapsed ? "»" : "«"}
        </button>
      </div>

      <nav className="space-y-1 px-2 pb-6">
        {items.map(it => {
          const active = pathname === it.href;
          return (
            <Link
              key={it.href}
              href={it.href}
              className={cx(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                collapsed && "justify-center"
              )}
              title={collapsed ? it.label : undefined}
            >
              <span className="text-base">{it.emoji}</span>
              <span className={cx(collapsed && "sr-only")}>{it.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
