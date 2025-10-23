"use client";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { listSources } from "@/modules/loom/services/sources";
import { searchEntries, updateEntry, deleteEntry, bulkReplace } from "@/modules/loom/services/entries";
import Combobox from "../shared/Combobox";

type Entry = { id: number|string; text: string; translation: string; source_name?: string; created_at?: string; };
type Order = "asc" | "desc";

function cls(...xs: Array<string | false | null | undefined>) { return xs.filter(Boolean).join(" "); }

function applyOrder(items: Entry[], order: Order): Entry[] {
  const clone = [...items];
  const toNum = (x: any) => {
    const n = Number(x);
    return Number.isFinite(n) ? n : Number(String(x).replace(/[^\d.-]/g, "")) || 0;
  };
  clone.sort((a,b) => {
    const da = toNum(a.id), db = toNum(b.id);
    return order === "asc" ? da - db : db - da;
  });
  return clone;
}

export default function ManagePanel(){
  const [tab, setTab] = useState<"basic"|"advanced"|"bulk">("basic");
  const [q, setQ] = useState("");
  const [order, setOrder] = useState<Order>("desc");
  const [source, setSource] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [adv, setAdv] = useState({keywords:"", sourceSelect:"", regex:false, exact:false});
  const [bulk, setBulk] = useState({scopeSource:"", scopeQuery:"", field:"both", find:"", replace:"", regex:false, case:false, dryRun:true} as any);
  const [bulkMsg, setBulkMsg] = useState("");

  const [items, setItems] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string>("");
  const [expandedId, setExpandedId] = useState<string | number | null>(null);

  const { data: sources = [] } = useQuery({ queryKey: ["loom","sources"], queryFn: () => listSources(), staleTime: 60_000 });

  const loadBasic = useCallback(async (reset=false)=>{
    setLoading(true); setErr("");
    try {
      const curPage = reset ? 1 : page;
      const { items, total } = await searchEntries({
        q: q.trim() || undefined,
        source_name: source || undefined,
        limit: pageSize, offset: (curPage-1)*pageSize,
        order_by:"id", order
      });
      setItems(applyOrder(items, order));
      setTotal(total);
      if (reset) setPage(1);
      if (expandedId && !items.some(x=>String(x.id)===String(expandedId))) setExpandedId(null);
    } catch (e:any) { setErr(e?.message || "加载失败"); setItems([]); setTotal(0); }
    finally { setLoading(false); }
  }, [q, source, page, pageSize, expandedId, order]);

  const loadAdvanced = useCallback(async (reset=false)=>{
    setLoading(true); setErr("");
    try {
      const curPage = reset ? 1 : page;
      const { items, total } = await searchEntries({
        q: adv.keywords || undefined, source_name: adv.sourceSelect || undefined,
        regex: adv.regex || undefined, exact: adv.exact || undefined,
        limit: pageSize, offset: (curPage-1)*pageSize, order_by:"id", order
      });
      setItems(applyOrder(items, order));
      setTotal(total);
      if (reset) setPage(1);
      if (expandedId && !items.some(x=>String(x.id)===String(expandedId))) setExpandedId(null);
    } catch (e:any) { setErr(e?.message || "加载失败"); setItems([]); setTotal(0); }
    finally { setLoading(false); }
  }, [adv, page, pageSize, expandedId, order]);

  useEffect(()=>{ loadBasic(true); }, []);
  useEffect(()=>{ const run = tab==="basic" ? loadBasic : tab==="advanced" ? loadAdvanced : null; if (run) run(false); }, [page, pageSize]);
  useEffect(()=>{ if (tab==="basic") loadBasic(true); }, [q, source, tab, order]);
  useEffect(()=>{ if (tab==="advanced") loadAdvanced(true); }, [adv, tab, order]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const runBulk = useCallback(async ()=>{
    setBulkMsg("正在执行…");
    try {
      const ok = await bulkReplace({
        source_name: bulk.scopeSource || undefined,
        q: bulk.scopeQuery || undefined,
        field: bulk.field, find: bulk.find, replace: bulk.replace,
        regex: bulk.regex, case: bulk.case, dry_run: bulk.dryRun
      });
      setBulkMsg(ok ? "完成" : "批量操作失败");
      if (ok && !bulk.dryRun) { if (tab === "basic") await loadBasic(true); if (tab === "advanced") await loadAdvanced(true); }
    } catch(e:any){ setBulkMsg(e?.message || "批量操作失败"); }
  }, [bulk, tab, loadBasic, loadAdvanced]);

  return (
    <div className="max-w-5xl">
      <div className="flex items-center gap-6 text-sm">
        <button className={cls("px-2 py-2 border-b-2", tab==="basic"?"border-rose-500 text-rose-600":"border-transparent")} onClick={()=>setTab("basic")}>出处搜索</button>
        <button className={cls("px-2 py-2 border-b-2", tab==="advanced"?"border-rose-500 text-rose-600":"border-transparent")} onClick={()=>setTab("advanced")}>多重筛选</button>
        <button className={cls("px-2 py-2 border-b-2", tab==="bulk"?"border-rose-500 text-rose-600":"border-transparent")} onClick={()=>setTab("bulk")}>批量修改</button>
        <div className="ml-auto flex items-center gap-3 py-3">
          <span className="text-gray-600">共 {total} 条</span>
          <label className="flex items-center gap-1">
            <span className="text-gray-600">每页</span>
            <select className="rounded border px-2 py-1" value={pageSize} onChange={(e)=>{ setPageSize(parseInt(e.target.value)); setPage(1); }}>
              {[10,20,30,50,80].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        </div>
      </div>

      {tab==="basic" && (
        <section className="mt-4 space-y-3">
          <div className="flex flex-wrap items-center gap-3">
            <input className="rounded border px-3 py-2 min-w-[260px] flex-1" placeholder="关键词（可留空，仅按来源查找）" value={q} onChange={(e)=>setQ(e.target.value)} onKeyDown={(e)=>{ if(e.key==="Enter"){ setPage(1); loadBasic(true); } }} />
            <label className="text-sm text-gray-600">ID 排序</label>
            <select className="rounded border px-3 py-2" value={order} onChange={(e)=>setOrder(e.target.value as Order)}>
              <option value="desc">倒序（新 → 旧）</option>
              <option value="asc">正序（旧 → 新）</option>
            </select>
            <button onClick={()=>{ setPage(1); loadBasic(true); }} className="rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">搜索</button>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm text-gray-600">来源</label>
            <Combobox value={source} onChange={setSource} options={(sources as any) || []} />
          </div>
        </section>
      )}

      {tab==="advanced" && (
        <section className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Keyword(s)</label>
              <input className="w-full rounded border px-3 py-2" value={adv.keywords} onChange={(e)=>setAdv({...adv, keywords: e.target.value})} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm text-gray-600 mb-1">Source filter</label>
              <Combobox value={adv.sourceSelect} onChange={(v)=>setAdv({...adv, sourceSelect: v})} options={(sources as any) || []} />
            </div>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2"><input type="checkbox" checked={adv.regex} onChange={(e)=>setAdv({...adv, regex:e.target.checked})}/> <span>Regex</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={adv.exact} onChange={(e)=>setAdv({...adv, exact:e.target.checked})}/> <span>Exact</span></label>
            </div>
          </div>
          <div>
            <button onClick={()=>{ setPage(1); loadAdvanced(true); }} className="rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">Run Search</button>
          </div>
        </section>
      )}

      {tab==="bulk" && (
        <section className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm text-gray-600 mb-1">Scope: Source (optional)</label>
              <Combobox value={bulk.scopeSource} onChange={(v)=>setBulk({...bulk, scopeSource: v})} options={(sources as any) || []} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Scope: Keyword filter (optional)</label>
              <input className="w-full rounded border px-3 py-2" value={bulk.scopeQuery} onChange={(e)=>setBulk({...bulk, scopeQuery: e.target.value})} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Field</label>
              <select className="w-full rounded border px-3 py-2" value={bulk.field} onChange={(e)=>setBulk({...bulk, field: e.target.value as any})}>
                <option value="both">Both (原文与译文)</option>
                <option value="src">Only 原文</option>
                <option value="tgt">Only 译文</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Find</label>
                <input className="w-full rounded border px-3 py-2" value={bulk.find} onChange={(e)=>setBulk({...bulk, find: e.target.value})} />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Replace</label>
                <input className="w-full rounded border px-3 py-2" value={bulk.replace} onChange={(e)=>setBulk({...bulk, replace: e.target.value})} />
              </div>
            </div>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2"><input type="checkbox" checked={bulk.regex} onChange={(e)=>setBulk({...bulk, regex:e.target.checked})}/> <span>Regex</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={bulk.case} onChange={(e)=>setBulk({...bulk, case:e.target.checked})}/> <span>Case</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={bulk.dryRun} onChange={(e)=>setBulk({...bulk, dryRun:e.target.checked})}/> <span>Dry-run</span></label>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button onClick={runBulk} className="rounded px-4 py-2 bg-blue-600 text-white hover:bg-blue-700">执行批量修改</button>
            <span className="text-sm text-gray-600">{bulkMsg}</span>
          </div>
        </section>
      )}

      <div className="space-y-5 mt-4">
        {loading && <div className="text-center text-gray-500 py-8">加载中…</div>}
        {!loading && items.length===0 && <div className="text-center text-gray-500 py-8">暂无数据</div>}
        {!loading && items.map((e, idx)=>(
          <ItemWithInlineEditor key={String(e.id)} entry={e} index={(page-1)*pageSize + idx + 1}
            expanded={String(expandedId)===String(e.id)}
            onOpen={()=>setExpandedId(e.id)} onClose={()=>setExpandedId(null)}
            onSaved={()=>{ tab==="basic" ? loadBasic(false) : loadAdvanced(false); }}
            onDeleted={()=>{ tab==="basic" ? loadBasic(false) : loadAdvanced(false); }} />
        ))}
      </div>

      <div className="mt-6 flex items-center justify-between">
        <div className="text-sm text-gray-600">页 {page} / {totalPages}</div>
        <div className="flex items-center gap-2">
          <button disabled={page<=1} onClick={()=>setPage(p=>Math.max(1,p-1))} className={cls("rounded px-3 py-2", page<=1 ? "bg-gray-200 text-gray-500" : "bg-gray-800 text-white hover:bg-black")}>上一页</button>
          <button disabled={page>=totalPages} onClick={()=>setPage(p=>Math.min(totalPages,p+1))} className={cls("rounded px-3 py-2", page>=totalPages ? "bg-gray-200 text-gray-500" : "bg-gray-800 text-white hover:bg-black")}>下一页</button>
        </div>
      </div>
    </div>
  );
}

function ItemWithInlineEditor({
  entry, index, expanded, onOpen, onClose, onSaved, onDeleted
}: {
  entry: Entry; index: number;
  expanded: boolean;
  onOpen: () => void; onClose: () => void;
  onSaved: () => void; onDeleted: () => void;
}){
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  useEffect(()=>{
    const onDoc = (e: MouseEvent) => { if (!menuRef.current) return; if (!menuRef.current.contains(e.target as Node)) setMenuOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return ()=>{ document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  },[]);

  const [src, setSrc] = useState<string>(entry.text || "");
  const [tgt, setTgt] = useState<string>(entry.translation || "");
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  const editRef = useRef<HTMLDivElement | null>(null);
  useEffect(()=>{
    const onDoc = (e: MouseEvent) => {
      if (!expanded) return;
      if (!editRef.current) return;
      if (!editRef.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener("mousedown", onDoc);
    return ()=>document.removeEventListener("mousedown", onDoc);
  }, [expanded, onClose]);

  const save = useCallback(async ()=>{
    setSaving(true); setErr("");
    try { await updateEntry(entry.id, { text: src, translation: tgt }); onSaved(); onClose(); }
    catch(e:any){ setErr(e?.message || "保存失败"); }
    finally { setSaving(false); }
  }, [entry.id, src, tgt, onSaved, onClose]);

  const remove = useCallback(async ()=>{
    if (!confirm("确认删除该条目？")) return;
    try { await deleteEntry(entry.id); onDeleted(); }
    catch(e:any){ alert(e?.message || "删除失败"); }
  }, [entry.id, onDeleted]);

  return (
    <div className="wl-card rounded-lg overflow-hidden">
      <div className="px-4 py-3">
        <div className="flex items-start gap-3">
          <div className="text-sm text-gray-500 w-8 shrink-0">#{index}</div>
          <div className="min-w-0 flex-1">
            <div className="text-[13px] text-gray-500 mb-1">
              <span className="mr-3">ID: {String(entry.id)}</span>
              <span>来源：{entry.source_name ?? ""}</span>
              <span className="ml-3">{(entry.created_at ?? "").replace?.("T"," ").slice?.(0,19)}</span>
            </div>
            <div className="font-medium text-gray-900 whitespace-pre-wrap">{entry.text}</div>
            <div className="text-gray-700 whitespace-pre-wrap mt-1">{entry.translation}</div>
          </div>

          <div className="ml-auto relative" ref={menuRef}>
            <button className="rounded-md border px-2 py-1 hover:bg-gray-50" onClick={()=>setMenuOpen(v=>!v)} title="更多">⋯</button>
            {menuOpen && (
              <div className="absolute right-0 mt-2 w-36 rounded-md border bg-white shadow-lg z-20">
                <button className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={()=>{ setMenuOpen(false); onOpen(); }}>✏️ 编辑</button>
                <button className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50" onClick={()=>{ alert("计时器占位，可接入你的番茄/倒计时模块"); setMenuOpen(false); }}>⏱ 计时器</button>
                <button className="block w-full text-left px-3 py-2 text-sm hover:bg-gray-50 text-red-600" onClick={()=>{ setMenuOpen(false); remove(); }}>🗑 删除</button>
              </div>
            )}
          </div>
        </div>
      </div>

      {expanded && (
        <div ref={editRef} className="border-t bg-gray-50/60 px-4 py-3">
          <div className="flex gap-3 text-sm mb-2">
            <span className="text-gray-600">编辑</span>
            <span className="text-gray-400">|</span>
            <span className="text-gray-500">历史（占位）</span>
          </div>
          <div className="space-y-3">
            <div>
              <div className="text-sm text-gray-700 mb-1">原文</div>
              <textarea className="w-full min-h-28 rounded border px-3 py-2" value={src} onChange={(e)=>setSrc(e.target.value)} />
            </div>
            <div>
              <div className="text-sm text-gray-700 mb-1">译文</div>
              <textarea className="w-full min-h-28 rounded border px-3 py-2" value={tgt} onChange={(e)=>setTgt(e.target.value)} />
            </div>
            {err && <div className="text-sm text-red-700">{err}</div>}
            <div className="flex items-center gap-2">
              <button className="rounded border px-3 py-1 hover:bg-white" onClick={onClose}>取消</button>
              <button className={cls("rounded px-3 py-1", saving ? "bg-gray-300 text-gray-600" : "bg-blue-600 text-white hover:bg-blue-700")} onClick={save} disabled={saving}>
                {saving ? "保存中…" : "保存"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
