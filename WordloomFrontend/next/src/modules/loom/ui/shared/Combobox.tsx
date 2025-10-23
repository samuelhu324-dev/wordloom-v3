"use client";
import React, { useEffect, useMemo, useRef, useState } from "react";

type SourceItem = { id?: string|number; name: string };

function cls(...xs: Array<string | false | null | undefined>) { return xs.filter(Boolean).join(" "); }

export default function Combobox({
  value, onChange, options, placeholder="选择一个来源（可输入过滤）", widthClass="w-full md:w-[820px]"
}: { value: string; onChange: (v: string)=>void; options: SourceItem[]; placeholder?: string; widthClass?: string; }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState<string>(value || "");
  const [activeIndex, setActiveIndex] = useState(0);
  const rootRef = useRef<HTMLDivElement|null>(null);
  const listRef = useRef<HTMLDivElement|null>(null);

  useEffect(()=>{ setQuery(value || ""); }, [value]);

  useEffect(()=>{
    const onDoc = (e: MouseEvent) => { if (!rootRef.current) return; if (!rootRef.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    return ()=>document.removeEventListener("mousedown", onDoc);
  }, []);

  const filtered = useMemo(()=>{
    const arr = options || [];
    if (!query) return arr;
    const q = query.toLowerCase();
    return arr.filter(o => (o.name||"").toLowerCase().includes(q));
  }, [options, query]);

  useEffect(()=>{ setActiveIndex(0); }, [query, open]);

  const pick = (name: string) => { onChange(name); setQuery(name); setOpen(false); };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open && (e.key === "ArrowDown" || e.key === "Enter")) { setOpen(true); return; }
    if (!open) return;
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIndex(i=>Math.min(i+1, filtered.length-1)); scrollActiveIntoView(); }
    if (e.key === "ArrowUp")   { e.preventDefault(); setActiveIndex(i=>Math.max(i-1, 0)); scrollActiveIntoView(); }
    if (e.key === "Enter")     { e.preventDefault(); const x = filtered[activeIndex]; if (x) pick(x.name); }
    if (e.key === "Escape")    { setOpen(false); }
  };

  const scrollActiveIntoView = () => {
    requestAnimationFrame(()=>{
      const list = listRef.current; if (!list) return;
      const item = list.querySelector<HTMLElement>('[data-active="true"]');
      if (item) {
        const top = item.offsetTop, bottom = top + item.offsetHeight;
        if (top < list.scrollTop) list.scrollTop = top;
        else if (bottom > list.scrollTop + list.clientHeight) list.scrollTop = bottom - list.clientHeight;
      }
    });
  };

  return (
    <div className={cls("relative", widthClass)} ref={rootRef}>
      <div className={cls("flex items-center rounded border px-2", open ? "ring-2 ring-rose-400" : "")}>
        <input
          className="flex-1 px-2 py-2 outline-none bg-transparent"
          placeholder={placeholder}
          value={query}
          onChange={(e)=>{ setQuery(e.target.value); setOpen(true); }}
          onFocus={()=>setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {value && (
          <button type="button" className="px-2 py-2 text-gray-500" onClick={()=>{ onChange(""); setQuery(""); }} title="清除">✕</button>
        )}
        <button type="button" className="px-2 py-2 text-gray-600" onClick={()=>setOpen(o=>!o)} aria-label="toggle">▾</button>
      </div>
      {open && (
        <div ref={listRef} className="absolute z-30 mt-1 max-h-72 w-full overflow-y-auto rounded border bg-white shadow">
          {filtered.length === 0 && <div className="px-3 py-2 text-gray-500">无匹配来源</div>}
          {filtered.map((s, idx)=>{
            const active = idx === activeIndex;
            return (
              <div
                key={String(s.id ?? s.name)}
                data-active={active ? "true" : "false"}
                onMouseEnter={()=>setActiveIndex(idx)}
                onMouseDown={()=>pick(s.name)}
                className={cls("px-3 py-2 cursor-pointer truncate", active ? "bg-gray-100" : "hover:bg-gray-50")}
                title={s.name}
              >
                {s.name}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
