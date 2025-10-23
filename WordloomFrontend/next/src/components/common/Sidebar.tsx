"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

type Item = { key: string; href: string; label: string; emoji: string; };

const items: Item[] = [
  { key: "home", href: "/", label: "Home", emoji: "🏠" },
  { key: "loom", href: "/loom", label: "Loom", emoji: "📘" },
  { key: "orbit", href: "/orbit", label: "Orbit", emoji: "🪐" },
];

export default function Sidebar(){
  const pathname = usePathname();
  const [expanded, setExpanded] = useState(true);

  useEffect(()=>{
    const v = localStorage.getItem("wl_sidebar_expanded");
    if (v === "0") setExpanded(false);
  },[]);

  const toggle = () => {
    setExpanded(v=>{
      const nv = !v;
      localStorage.setItem("wl_sidebar_expanded", nv ? "1" : "0");
      return nv;
    });
  };

  return (
    <aside className={`shrink-0 border-r bg-white transition-all ${expanded ? "w-56" : "w-16"}`} style={{borderColor:"var(--border)"}}>
      <div className="flex flex-col h-full">
        <div className="p-2">
          <button onClick={toggle} className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100">
            {expanded ? "«" : "»"}
          </button>
        </div>
        <nav className="flex-1 px-2 py-2 space-y-1">
          {items.map(it => {
            const active = pathname === it.href;
            return (
              <Link
                key={it.key}
                href={it.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${active ? "bg-rose-100 text-rose-700" : "hover:bg-gray-100"}`}
                title={expanded ? undefined : it.label}
              >
                <span className="text-xl" aria-hidden>{it.emoji}</span>
                {expanded && <span className="truncate">{it.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
