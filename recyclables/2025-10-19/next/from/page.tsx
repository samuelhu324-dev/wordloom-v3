"use client";

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

/* ========= shared ========= */
type Entry = {
  id: number | string;
  source_name?: string | null;
  created_at?: string | null;
  // text fields (compat)
  text?: string | null; translation?: string | null;
  en?: string | null; zh?: string | null;
  en_text?: string | null; zh_text?: string | null;
  src?: string | null; tgt?: string | null;
};

type SourceItem = { id: string; name: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

/* small utils */
const pickEn = (e: Entry) => e.text ?? e.en ?? e.en_text ?? e.src ?? "";
const pickZh = (e: Entry) => e.translation ?? e.zh ?? e.zh_text ?? e.tgt ?? "";
const cls = (...xs: Array<string | false | null | undefined>) => xs.filter(Boolean).join(" ");

/* ========= sources ========= */
async function fetchSources(q = "", limit = 200): Promise<SourceItem[]> {
  const candidates = [
    `${API_BASE}/sources?limit=${limit}&q=${encodeURIComponent(q)}`,
    `${API_BASE}/sources/?limit=${limit}&q=${encodeURIComponent(q)}`,
    `${API_BASE}/sources/list?limit=${limit}&q=${encodeURIComponent(q)}`,
  ];
  for (const u of candidates) {
    try {
      const r = await fetch(u, { cache: "no-store" });
      if (!r.ok) continue;
      const data = await r.json();
      if (Array.isArray(data) && (data.length === 0 || typeof data[0] === "string")) {
        const arr = (data as string[]).map(s => ({ id: s, name: s }))
          .sort((a,b)=>a.name.localeCompare(b.name,"en"));
        return q ? arr.filter(s=>s.name.toLowerCase().includes(q.toLowerCase())).slice(0,limit) : arr.slice(0,limit);
      }
      const arr = (Array.isArray(data) ? data : (data?.items ?? data?.results ?? [])) as any[];
      if (arr.length) {
        const mapped = arr.map(x => {
          if (typeof x === "string") return { id: x, name: x };
          const id = String(x.id ?? x.source_id ?? x.name ?? x.source_name ?? "");
          const name = String(x.name ?? x.source_name ?? x.label ?? id);
          return { id, name };
        }).filter(x=>x.id && x.name);
        const filtered = q ? mapped.filter(s=>s.name.toLowerCase().includes(q.toLowerCase())) : mapped;
        return filtered.sort((a,b)=>a.name.localeCompare(b.name,"en")).slice(0,limit);
      }
    } catch {}
  }
  // fallback from entries
  try {
    const r = await fetch(`${API_BASE}/entries/search?limit=1000`, { cache: "no-store" });
    if (!r.ok) return [];
    const data = await r.json();
    const items: any[] = Array.isArray(data) ? data : (data.items ?? []);
    const set = new Set<string>();
    for (const it of items) {
      const name = it.source_name ?? it.source ?? null;
      if (name) set.add(String(name));
    }
    return Array.from(set).map(s=>({id:s,name:s})).sort((a,b)=>a.name.localeCompare(b.name,"en")).slice(0,limit);
  } catch { return []; }
}

/* ========= entries ========= */
async function searchBySource(source_name: string, limit=50, offset=0): Promise<{items:Entry[], total:number}> {
  const url = new URL(`${API_BASE}/entries/search`, window.location.href);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  if (source_name) url.searchParams.set("source_name", source_name);
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const data = await r.json();
  const items: Entry[] = Array.isArray(data?.items) ? data.items : (Array.isArray(data) ? data : []);
  const total = typeof data?.total === "number" ? data.total : items.length;
  return { items, total };
}

/* robust write APIs that try several endpoints */
async function updateEntry(id: number|string, payload: {src?:string,tgt?:string,source_name?:string}) {
  const candidates: Array<() => Promise<Response>> = [
    () => fetch(`${API_BASE}/entries/${id}`, { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)}),
    () => fetch(`${API_BASE}/entries/${id}`, { method: "PUT",   headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload)}),
    () => fetch(`${API_BASE}/entries/update`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ id, ...payload })}),
  ];
  for (const run of candidates) {
    try {
      const r = await run();
      if (r.ok) return await r.json().catch(()=>({ ok:true }));
    } catch {}
  }
  throw new Error("更新失败：没有可用的 entries 更新接口");
}

async function deleteEntry(id: number|string) {
  const candidates: Array<() => Promise<Response>> = [
    () => fetch(`${API_BASE}/entries/${id}`, { method: "DELETE" }),
    () => fetch(`${API_BASE}/entries/delete`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ id }) }),
  ];
  for (const run of candidates) {
    try { const r = await run(); if (r.ok) return true; } catch {}
  }
  throw new Error("删除失败：没有可用的 entries 删除接口");
}

/* ========= Page ========= */
export default function FromPage() {
  const [elevated, setElevated] = useState(false);
  useEffect(()=>{
    const f=()=>setElevated(window.scrollY>8);
    f(); window.addEventListener("scroll", f, {passive:true}); return ()=>window.removeEventListener("scroll", f);
  },[]);

  const [source, setSource] = useState<string>("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const { data: sourceList=[] } = useQuery({
    queryKey: ["sources","from"],
    queryFn: ()=>fetchSources(""),
    staleTime: 30_000,
  });

  const [items, setItems] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const load = useCallback(async (reset=false)=>{
    setLoading(true); setMsg("");
    try {
      const curPage = reset ? 1 : page;
      const { items, total } = await searchBySource(source, pageSize, (curPage-1)*pageSize);
      setItems(items); setTotal(total); if (reset) setPage(1);
    } catch(e:any) {
      setMsg(e?.message || "加载失败");
      setItems([]); setTotal(0);
    } finally { setLoading(false); }
  },[source,page,pageSize]);

  useEffect(()=>{ load(true); }, [source]);
  useEffect(()=>{ load(false); }, [page, pageSize]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-semibold mb-4">From — Browse & Inline Edit</h1>

      {/* top bar */}
      <div className={cls("sticky top-0 z-30 backdrop-blur bg-white/80 border-b", elevated && "shadow-sm")}>
        <div className="py-3 flex flex-wrap gap-3 items-center">
          {/* source select */}
          <label className="text-sm text-gray-600">选择来源（不选 → 显示最新 {pageSize} 条）</label>
          <select className="rounded border px-3 py-2"
            value={source}
            onChange={(e)=>{ setSource(e.target.value); }}
          >
            <option value="">（不选）</option>
            {sourceList.map(s=>(<option key={s.id} value={s.name}>{s.name}</option>))}
          </select>

          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-gray-600">共 {total} 条</span>
            <label className="flex items-center gap-1">
              <span className="text-gray-600">每页</span>
              <select className="rounded border px-2 py-1" value={pageSize} onChange={(e)=>{ setPageSize(parseInt(e.target.value)); setPage(1); }}>
                {[10,20,30,50].map(n => <option key={n} value={n}>{n}</option>)}
              </select>
            </label>
          </div>
        </div>
      </div>

      {msg && <div className="mt-3 mb-2 rounded border bg-yellow-50 text-gray-800 px-3 py-2 text-sm">{msg}</div>}

      {/* list */}
      <div className="space-y-4 mt-4">
        {loading && <div className="text-center text-gray-500 py-8">加载中…</div>}
        {!loading && items.map((e, idx)=>(
          <EditableCard key={String(e.id)} entry={e} index={(page-1)*pageSize + idx + 1} onSaved={load} onDeleted={load} />
        ))}
        {!loading && items.length===0 && <div className="text-center text-gray-500 py-8">暂无数据</div>}
      </div>

      {/* pager */}
      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">页 {page} / {Math.max(1, Math.ceil(total / pageSize))}</div>
        <div className="flex items-center gap-2">
          <button disabled={page<=1} onClick={()=>setPage(p=>Math.max(1,p-1))} className={cls("rounded px-3 py-2", page<=1 ? "bg-gray-200 text-gray-500" : "bg-gray-800 text-white hover:bg-black")}>上一页</button>
          <button disabled={page>=Math.max(1, Math.ceil(total / pageSize))} onClick={()=>setPage(p=>p+1)} className={cls("rounded px-3 py-2", page>=Math.max(1, Math.ceil(total / pageSize)) ? "bg-gray-200 text-gray-500" : "bg-gray-800 text-white hover:bg-black")}>下一页</button>
        </div>
      </div>
    </div>
  );
}

/* ===== inline editor card ===== */
function EditableCard({ entry, index, onSaved, onDeleted }: { entry: Entry; index: number; onSaved: ()=>void; onDeleted: ()=>void; }) {
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState<"edit"|"history">("edit");
  const [src, setSrc] = useState<string>(pickEn(entry));
  const [tgt, setTgt] = useState<string>(pickZh(entry));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const onSave = useCallback(async ()=>{
    setSaving(true); setErr("");
    try {
      await updateEntry(entry.id, { src, tgt });
      onSaved();
    } catch(e:any) {
      setErr(e?.message || "保存失败");
    } finally { setSaving(false); }
  },[entry.id, src, tgt, onSaved]);

  const onDelete = useCallback(async ()=>{
    if (!confirm("确认删除该条目？")) return;
    try { await deleteEntry(entry.id); onDeleted(); } catch(e:any){ setErr(e?.message || "删除失败"); }
  },[entry.id, onDeleted]);

  return (
    <div className="rounded-lg border border-gray-200">
      <div className="px-4 py-3 flex items-center gap-3">
        <div className="text-sm text-gray-500">#{index}</div>
        <div className="text-sm">ID: {String(entry.id)}</div>
        <div className="ml-auto flex items-center gap-2">
          <button className="rounded border px-2 py-1" onClick={()=>setOpen(!open)}>{open ? "…" : "展开"}</button>
          <button className="rounded border px-2 py-1" title="删除" onClick={onDelete}>🗑</button>
        </div>
      </div>

      {open && (
        <div className="px-4 pb-4">
          <div className="text-sm text-gray-500">来源：{entry.source_name ?? ""}</div>
          <div className="text-sm text-gray-500">{(entry.created_at ?? "").replace?.("T"," ").slice?.(0,19)}</div>

          <div className="mt-3 border rounded">
            <div className="flex gap-3 px-3 py-2 bg-gray-50 text-sm">
              <button className={cls(tab==="edit"?"text-blue-700": "text-gray-600")} onClick={()=>setTab("edit")}>编辑</button>
              <button className={cls(tab==="history"?"text-blue-700": "text-gray-600")} onClick={()=>setTab("history")}>历史</button>
            </div>

            {tab==="edit" ? (
              <div className="p-3 space-y-3">
                <div>
                  <div className="text-sm text-gray-700 mb-1">原文</div>
                  <textarea className="w-full min-h-28 rounded border px-3 py-2" value={src} onChange={(e)=>setSrc(e.target.value)} />
                </div>
                <div>
                  <div className="text-sm text-gray-700 mb-1">译文</div>
                  <textarea className="w-full min-h-28 rounded border px-3 py-2" value={tgt} onChange={(e)=>setTgt(e.target.value)} />
                </div>
                {err && <div className="text-sm text-red-700">{err}</div>}
                <div className="flex items-center gap-3">
                  <button disabled={saving} onClick={onSave} className={cls("rounded px-4 py-2", saving ? "bg-gray-300 text-gray-600" : "bg-blue-600 text-white hover:bg-blue-700")}>
                    {saving ? "保存中…" : "保存"}
                  </button>
                </div>
              </div>
            ) : (
              <div className="p-3 text-sm text-gray-500">（历史功能占位：后端未提供 revision 接口时显示此文案）</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
