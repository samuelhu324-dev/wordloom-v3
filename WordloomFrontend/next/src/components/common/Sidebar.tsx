"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { createPortal } from "react-dom";
import { Home, FileText, Rocket, ChevronLeft, Menu } from "lucide-react";
// + 新增两个图标
import { BarChart3, Palette } from "lucide-react";

/** Sidebar.tsx — 可见可拉出的侧边栏（带全局按钮 + 小圆点可点 + 外侧手把） */

/** 固定宽度（可按需微调） */
const EXPANDED_W = 264;  // 展开宽度：图标 + 文字
const COLLAPSED_W = 72;  // 收起宽度：仅图标（始终可见）

/** 菜单项定义 */
type MenuItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
};

const ITEMS: MenuItem[] = [
  { label: "Home", href: "/", icon: Home },
  { label: "Loom", href: "/loom", icon: FileText },
  { label: "Orbit", href: "/orbit", icon: Rocket },
  // + 新增
  { label: "Stats", href: "/stats", icon: BarChart3 },
  { label: "Theme", href: "/theme", icon: Palette },
];

/** 顶角全局切换按钮：挂到 body，避免被任何 overflow/圆角裁剪 */
function GlobalToggleButton({
  collapsed,
  onToggle,
}: {
  collapsed: boolean;
  onToggle: () => void;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;

  return createPortal(
    <button
      onClick={onToggle}
      title={collapsed ? "展开菜单" : "收起菜单"}
      className="fixed left-3 top-3 z-[9999] h-10 w-10 rounded-full bg-card/90 border border-border/50 shadow-md
                 flex items-center justify-center backdrop-blur-sm hover:shadow-lg transition-all hover:scale-110"
    >
      {collapsed ? <Menu className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
    </button>,
    document.body
  );
}

export default function Sidebar() {
  // 替换为“折叠”唯一状态（不再使用 open/蒙层/抽屉）
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("sidebar-collapsed");
    const init = saved === "true";
    setCollapsed(init);
    document.documentElement.setAttribute("data-sidebar-state", init ? "closed" : "open");
  }, []);

  useEffect(() => {
    localStorage.setItem("sidebar-collapsed", String(collapsed));
    document.documentElement.setAttribute("data-sidebar-state", collapsed ? "closed" : "open");
  }, [collapsed]);

  const toggle = () => setCollapsed(v => !v);

  // 获取当前路径（客户端）
  const pathname = usePathname() || "/";

  // 辅助：判断是否为激活项
  const isActive = (href: string) =>
    pathname === href || (href !== "/" && pathname.startsWith(href));

  return (
    <>
      {/* 外侧灰色蒙层：已删除 */}
      {/* 窄导轨/外侧手把：已删除 */}

      {/* 圆角小圆标（唯一开关）：向右外移一点，跟随侧栏右边缘 */}
      <button
        type="button"
        aria-label="折叠/展开菜单"
        onClick={toggle}
        className="fixed top-3 z-[60] h-9 w-9 rounded-full border
                   bg-white/90 dark:bg-slate-900/80 border-black/10 dark:border-white/10
                   shadow-md hover:shadow-lg backdrop-blur flex items-center justify-center
                   text-slate-700 dark:text-slate-200"
        style={{
          // 紧贴侧栏外侧，并右移一点；可通过 --sidebar-fab-offset 调整
          left: "calc(var(--sidebar-w) + var(--sidebar-fab-offset, 10px))",
        }}
      >
        {/* 折叠/展开指示：≡ 或 ‹›，你可替换成图标库 */}
        <span className="text-sm select-none">{collapsed ? "»" : "«"}</span>
      </button>

      {/* 主侧栏：固定在左侧，可折叠 */}
      <aside
        className="app-sidebar"
        data-variant="glass"
        role="navigation"
        aria-label="Sidebar"
      >
        {/* 顶部：标题区（里面也可以再放一个开关按钮，非必须） */}
        <div className="h-14 px-4 flex items-center">
          <div className="font-semibold tracking-tight opacity-80">Wordloom</div>
        </div>

        <div className="mx-3 my-2 h-px bg-black/10 dark:bg-white/10" />

        {/* 导航区：请确保文字包在 <span className="label"> 中，折叠时会自动隐藏 */}
        <nav className="px-3 py-2 space-y-1">
          {ITEMS.map((it) => {
            const active = isActive(it.href); // 替换原先直接用 pathname 的地方
            return (
              <Link key={it.href} href={it.href} aria-current={active ? "page" : undefined}>
                <div className="group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all">
                  <div className="h-5 w-5 shrink-0">
                    <it.icon />
                  </div>
                  <span className="text-sm font-medium">{it.label}</span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* ...existing code... 底部信息/版本等 */}
      </aside>
    </>
  );
}
