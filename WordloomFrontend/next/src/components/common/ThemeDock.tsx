"use client";
import { useEffect, useState } from "react";

const THEMES = [
  { key: "sky", label: "sky", emoji: "🔮" },
  { key: "indigo", label: "indigo", emoji: "🟣" },
  { key: "maroon", label: "maroon", emoji: "🍷" },
  { key: "lavender", label: "lavender", emoji: "💜" },
  { key: "forest", label: "forest", emoji: "🌿" },
  { key: "sunset", label: "sunset", emoji: "🌇" },
  { key: "ocean", label: "ocean", emoji: "🌊" },
];

function applyTheme(t: string){
  const root = document.documentElement;
  THEMES.forEach(x => root.classList.remove("theme-"+x.key));
  root.classList.add("theme-"+t);
}

export default function ThemeDock(){
  const [theme, setTheme] = useState<string>("indigo");
  useEffect(()=>{
    const saved = localStorage.getItem("wl_theme");
    const t = saved && THEMES.some(x=>x.key===saved) ? saved : "indigo";
    setTheme(t); applyTheme(t);
  },[]);

  const pick = (t: string)=>{
    setTheme(t); applyTheme(t); localStorage.setItem("wl_theme", t);
  };

  return (
    <div className="fixed bottom-4 left-3 z-40">
      <div className="rounded-2xl shadow border bg-white/90 backdrop-blur px-2 py-2 flex gap-1 items-center">
        {THEMES.map(th => (
          <button key={th.key} onClick={()=>pick(th.key)}
            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm ${theme===th.key ? "ring-2 ring-[var(--accent)]" : ""}`}
            title={th.label} aria-label={th.label}>
            <span aria-hidden>{th.emoji}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
