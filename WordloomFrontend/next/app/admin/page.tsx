"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";

/* ========================
   类型 & 工具
   ======================== */
type Entry = {
  id: number | string;
  source_name?: string | null;
  created_at?: string | null;
  // 兼容历史字段
  text?: string | null; translation?: string | null;
  en?: string | null; zh?: string | null;
  en_text?: string | null; zh_text?: string | null;
  src?: string | null; tgt?: string | null;
};

type SourceItem = { id: string; name: string };

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

const cls = (...xs: Array<string | false | null | undefined>) => xs.filter(Boolean).join(" ");
const pickEn = (e: Entry) => e.text ?? e.en ?? e.en_text ?? e.src ?? "";
const pickZh = (e: Entry) => e.translation ?? e.zh ?? e.zh_text ?? e.tgt ?? "";

/* ========================
   来源加载（含兜底）
   ======================== */
async function fetchSources(q = "", limit = 200): Promise<SourceItem[]> {
  const endpoints = [
    `${API_BASE}/sources?limit=${limit}&q=${encodeURIComponent(q)}`,
    `${API_BASE}/sources/?limit=${limit}&q=${encodeURIComponent(q)}`,
    `${API_BASE}/sources/list?limit=${limit}&q=${encodeURIComponent(q)}`,
  ];
  for (const u of endpoints) {
    try {
      const r = await fetch(u, { cache: "no-store" });
      if (!r.ok) continue;
      const data = await r.json();
      if (Array.isArray(data) && (data.length === 0 || typeof data[0] === "string")) {
        const arr = (data as string[]).map(s=>({id:s,name:s}));
        const filter = q ? arr.filter(s=>s.name.toLowerCase().includes(q.toLowerCase())) : arr;
        return filter.sort((a,b)=>a.name.localeCompare(b.name,"en")).slice(0,limit);
      }
      const arr = (Array.isArray(data) ? data : (data?.items ?? data?.results ?? [])) as any[];
      if (arr.length) {
        const mapped = arr.map(x=>{
          if (typeof x === "string") return {id:x, name:x};
          const id = String(x.id ?? x.source_id ?? x.name ?? x.source_name ?? "");
          const name = String(x.name ?? x.source_name ?? x.label ?? id);
          return { id, name };
        }).filter(x=>x.id && x.name);
        const filter = q ? mapped.filter(s=>s.name.toLowerCase().includes(q.toLowerCase())) : mapped;
        return filter.sort((a,b)=>a.name.localeCompare(b.name,"en")).slice(0,limit);
      }
    } catch {}
  }
  // 兜底：从 entries 聚合
  try {
    const r = await fetch(`${API_BASE}/entries/search?limit=1000&offset=0`, { cache: "no-store" });
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

/* ========================
   搜索（关键词 + 来源）
   ======================== */
async function searchEntries(params: Record<string, string | number | boolean | undefined>) {
  const url = new URL(`${API_BASE}/entries/search`, window.location.href);
  Object.entries(params).forEach(([k,v])=>{
    if (v === undefined || v === "" || v === null) return;
    url.searchParams.set(k, String(v));
  });
  const r = await fetch(url.toString(), { cache: "no-store" });
  if (!r.ok) throw new Error("HTTP " + r.status);
  const data = await r.json();
  const items: Entry[] = Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : [];
  const total = typeof data?.total === "number" ? data.total : items.length;
  return { items, total };
}

/* ========================
   写接口（多候选）
   ======================== */
async function updateEntry(id: number|string, payload: {src?:string,tgt?:string,source_name?:string}) {
  const candidates: Array<() => Promise<Response>> = [
    () => fetch(`${API_BASE}/entries/${id}`, { method: "PATCH", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) }),
    () => fetch(`${API_BASE}/entries/${id}`, { method: "PUT",   headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) }),
    () => fetch(`${API_BASE}/entries/update`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ id, ...payload }) }),
  ];
  for (const run of candidates) {
    try {
      const r = await run();
      if (r.ok) return await r.json().catch(()=>({ ok:true }));
    } catch {}
  }
  throw new Error("保存失败：未找到可用更新端点");
}

async function deleteEntry(id: number|string) {
  const candidates: Array<() => Promise<Response>> = [
    () => fetch(`${API_BASE}/entries/${id}`, { method: "DELETE" }),
    () => fetch(`${API_BASE}/entries/delete`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify({ id }) }),
  ];
  for (const run of candidates) {
    try { const r = await run(); if (r.ok) return true; } catch {}
  }
  throw new Error("删除失败：未找到可用删除端点");
}

async function bulkReplace(payload: any) {
  const candidates: Array<() => Promise<Response>> = [
    () => fetch(`${API_BASE}/entries/bulk_replace`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) }),
    () => fetch(`${API_BASE}/entries/bulk-replace`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) }),
    () => fetch(`${API_BASE}/entries/replace`, { method: "POST", headers: {"Content-Type":"application/json"}, body: JSON.stringify(payload) }),
  ];
  for (const run of candidates) {
    try { const r = await run(); if (r.ok) return await r.json().catch(()=>({ok:true})); } catch {}
  }
  throw new Error("未找到可用的批量替换接口");
}

/* ========================
   页面：列表 + 行内折叠编辑 + 顶部粘性菜单（三工具）
   ======================== */
export default function AdminInlineEditorPage() {
  const [elevated, setElevated] = useState(false);
  useEffect(()=>{
    const f=()=>setElevated(window.scrollY>8);
    f(); window.addEventListener("scroll", f, { passive:true });
    return ()=>window.removeEventListener("scroll", f);
  },[]);

  // 菜单 tab：basic / advanced / bulk
  const [tab, setTab] = useState<"basic"|"advanced"|"bulk">("basic");

  // 顶栏：关键词 + 来源 + 每页（basic）
  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // 高级筛选
  const [adv, setAdv] = useState({
    keywords: "",
    srcLang: "auto",
    tgtLang: "auto",
    case: false,
    regex: false,
    exact: false,
    sourceSelect: "",
    sourceType: "",
    timeRange: "all",
  });

  // 批量替换
  const [bulk, setBulk] = useState({
    scopeSource: "",
    scopeQuery: "",
    field: "both",
    find: "",
    replace: "",
    regex: false,
    case: false,
    dryRun: true,
  });
  const [bulkMsg, setBulkMsg] = useState("");

  // 列表
  const [items, setItems] = useState<Entry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string>("");

  // 当前展开编辑的条目ID；同时只允许一个展开
  const [expandedId, setExpandedId] = useState<string | number | null>(null);

  // 来源下拉
  const { data: sources = [] } = useQuery({
    queryKey: ["sources","inline"],
    queryFn: () => fetchSources(""),
    staleTime: 30_000,
  });

  const loadBasic = useCallback(async (reset=false)=>{
    setLoading(true); setErr("");
    try {
      const curPage = reset ? 1 : page;
      const { items, total } = await searchEntries({ q: q.trim() || undefined, source_name: source || undefined, limit: pageSize, offset: (curPage-1)*pageSize });
      setItems(items); setTotal(total);
      if (reset) setPage(1);
      if (expandedId && !items.some(x=>String(x.id)===String(expandedId))) setExpandedId(null);
    } catch (e:any) {
      setErr(e?.message || "加载失败"); setItems([]); setTotal(0);
    } finally { setLoading(false); }
  }, [q, source, page, pageSize, expandedId]);

  const advToParams = useCallback(()=>{
    const params: Record<string, any> = {
      q: adv.keywords || undefined,
      source_name: adv.sourceSelect || undefined,
      source_like: adv.sourceType || undefined,
      case: adv.case || undefined,
      regex: adv.regex || undefined,
      exact: adv.exact || undefined,
      src_lang: adv.srcLang || undefined,
      tgt_lang: adv.tgtLang || undefined,
    };
    if (adv.timeRange && adv.timeRange !== "all") params["time"] = adv.timeRange;
    return params;
  }, [adv]);

  const loadAdvanced = useCallback(async (reset=false)=>{
    setLoading(true); setErr("");
    try {
      const curPage = reset ? 1 : page;
      const params = advToParams();
      const { items, total } = await searchEntries({ ...params, limit: pageSize, offset: (curPage-1)*pageSize });
      setItems(items); setTotal(total);
      if (reset) setPage(1);
      if (expandedId && !items.some(x=>String(x.id)===String(expandedId))) setExpandedId(null);
    } catch (e:any) {
      setErr(e?.message || "加载失败"); setItems([]); setTotal(0);
    } finally { setLoading(false); }
  }, [advToParams, page, pageSize, expandedId]);

  // 初次加载：basic
  useEffect(()=>{ loadBasic(true); }, []);
  // 翻页
  useEffect(()=>{
    const run = tab==="basic" ? loadBasic : tab==="advanced" ? loadAdvanced : null;
    if (run) run(false);
  }, [page, pageSize]);
  // 条件变更：重置页码并加载
  useEffect(()=>{ if (tab==="basic") loadBasic(true); }, [q, source, tab]);
  useEffect(()=>{ if (tab==="advanced") loadAdvanced(true); }, [adv, tab]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  // 批量替换
  const runBulk = useCallback(async ()=>{
    setBulkMsg("正在执行…");
    try {
      const payload = {
        source_name: bulk.scopeSource || undefined,
        q: bulk.scopeQuery || undefined,
        field: bulk.field,
        find: bulk.find,
        replace: bulk.replace,
        regex: bulk.regex,
        case: bulk.case,
        dry_run: bulk.dryRun,
      };
      const res = await bulkReplace(payload);
      setBulkMsg(`完成：${JSON.stringify(res).slice(0,400)}${JSON.stringify(res).length>400?"…":""}`);
      if (!bulk.dryRun) {
        // 执行后，刷新当前列表
        if (tab === "basic") await loadBasic(true);
        if (tab === "advanced") await loadAdvanced(true);
      }
    } catch(e:any){
      setBulkMsg(e?.message || "批量操作失败");
    }
  }, [bulk, tab, loadBasic, loadAdvanced]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-semibold mb-4">Admin — Inline Edit Below Item</h1>

      {/* 顶部粘顶菜单（三个工具） */}
      <div className={cls("sticky top-0 z-30 backdrop-blur bg-white/80 border-b", elevated && "shadow-sm")}>
        <div className="flex items-center gap-6 text-sm px-1">
          <ToolbarTab icon="📚" label="出处搜索" active={tab==="basic"} onClick={()=>{ setTab("basic"); }} />
          <ToolbarTab icon="🧭" label="多重筛选" active={tab==="advanced"} onClick={()=>{ setTab("advanced"); }} />
          <ToolbarTab icon="🛠" label="批量修改" active={tab==="bulk"} onClick={()=>{ setTab("bulk"); }} />
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
      </div>

      {/* 工具面板（紧贴菜单下方） */}
      {tab === "basic" && (
        <section className="mt-4">
          <div className="py-3 flex flex-wrap gap-3 items-center">
            <input
              className="rounded border px-3 py-2 min-w-[240px]"
              placeholder="关键词（可留空，仅按来源查找）"
              value={q}
              onChange={(e)=>setQ(e.target.value)}
              onKeyDown={(e)=>{ if(e.key==="Enter"){ setPage(1); loadBasic(true); } }}
            />
            <label className="text-sm text-gray-600">来源</label>
            <select className="rounded border px-3 py-2 min-w-[240px]" value={source} onChange={(e)=>{ setSource(e.target.value); }}>
              <option value="">（不选 → 最新）</option>
              {sources.map(s=>(<option key={s.id} value={s.name}>{s.name}</option>))}
            </select>

            <button onClick={()=>{ setPage(1); loadBasic(true); }} className="rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">搜索</button>
          </div>
        </section>
      )}

      {tab === "advanced" && (
        <section className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Keyword(s)</label>
              <input className="w-full rounded border px-3 py-2" value={adv.keywords} onChange={(e)=>setAdv({...adv, keywords: e.target.value})} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Source Lang</label>
                <select className="w-full rounded border px-3 py-2" value={adv.srcLang} onChange={(e)=>setAdv({...adv, srcLang: e.target.value})}>
                  {["auto","en","zh","ja","de","fr","es"].map(x=><option key={x} value={x}>{x}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Target Lang</label>
                <select className="w-full rounded border px-3 py-2" value={adv.tgtLang} onChange={(e)=>setAdv({...adv, tgtLang: e.target.value})}>
                  {["auto","zh","en","ja","de","fr","es"].map(x=><option key={x} value={x}>{x}</option>)}
                </select>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <label className="flex items-center gap-2"><input type="checkbox" checked={adv.case} onChange={(e)=>setAdv({...adv, case:e.target.checked})}/> <span>Case</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={adv.regex} onChange={(e)=>setAdv({...adv, regex:e.target.checked})}/> <span>Regex</span></label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={adv.exact} onChange={(e)=>setAdv({...adv, exact:e.target.checked})}/> <span>Exact</span></label>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Source filter (select)</label>
              <select className="w-full rounded border px-3 py-2" value={adv.sourceSelect} onChange={(e)=>setAdv({...adv, sourceSelect:e.target.value})}>
                <option value="">(Any)</option>
                {sources.map(s=>(<option key={s.id} value={s.name}>{s.name}</option>))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">or type (partial ok)</label>
              <input className="w-full rounded border px-3 py-2" value={adv.sourceType} onChange={(e)=>setAdv({...adv, sourceType:e.target.value})}/>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Time</label>
              <select className="w-full rounded border px-3 py-2" value={adv.timeRange} onChange={(e)=>setAdv({...adv, timeRange:e.target.value})}>
                <option value="all">All</option>
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="y2025">Year 2025</option>
                <option value="y2024">Year 2024</option>
                <option value="y2023">Year 2023</option>
              </select>
            </div>
          </div>
          <div>
            <button onClick={()=>{ setPage(1); loadAdvanced(true); }} className="rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">Run Search</button>
          </div>
        </section>
      )}

      {tab === "bulk" && (
        <section className="mt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">Scope: Source (optional)</label>
              <select className="w-full rounded border px-3 py-2" value={bulk.scopeSource} onChange={(e)=>setBulk({...bulk, scopeSource:e.target.value})}>
                <option value="">(All)</option>
                {sources.map(s=>(<option key={s.id} value={s.name}>{s.name}</option>))}
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Scope: Keyword filter (optional)</label>
              <input className="w-full rounded border px-3 py-2" value={bulk.scopeQuery} onChange={(e)=>setBulk({...bulk, scopeQuery:e.target.value})} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">Field</label>
              <select className="w-full rounded border px-3 py-2" value={bulk.field} onChange={(e)=>setBulk({...bulk, field:e.target.value as any})}>
                <option value="both">Both (原文与译文)</option>
                <option value="src">Only 原文</option>
                <option value="tgt">Only 译文</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Find</label>
                <input className="w-full rounded border px-3 py-2" value={bulk.find} onChange={(e)=>setBulk({...bulk, find:e.target.value})} />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Replace</label>
                <input className="w-full rounded border px-3 py-2" value={bulk.replace} onChange={(e)=>setBulk({...bulk, replace:e.target.value})} />
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

      {/* 列表（原样保留：每项默认只读；右上三点 -> 编辑/删除；编辑在下面展开） */}
      <div className="space-y-5 mt-4">
        {loading && <div className="text-center text-gray-500 py-8">加载中…</div>}
        {!loading && items.length===0 && <div className="text-center text-gray-500 py-8">暂无数据</div>}
        {!loading && items.map((e, idx)=>(
          <ItemWithInlineEditor
            key={String(e.id)}
            entry={e}
            index={(page-1)*pageSize + idx + 1}
            expanded={String(expandedId)===String(e.id)}
            onOpen={()=>setExpandedId(e.id)}
            onClose={()=>setExpandedId(null)}
            onSaved={()=>{ tab==="basic" ? loadBasic(false) : loadAdvanced(false); }}
            onDeleted={()=>{ tab==="basic" ? loadBasic(false) : loadAdvanced(false); }}
          />
        ))}
      </div>

      {/* 分页 */}
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

/* ========================
   单条目 + 行内编辑组件（保持不变）
   ======================== */
function ItemWithInlineEditor({
  entry, index, expanded, onOpen, onClose, onSaved, onDeleted
}: {
  entry: Entry; index: number;
  expanded: boolean;
  onOpen: () => void; onClose: () => void;
  onSaved: () => void; onDeleted: () => void;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  useEffect(()=>{
    const onDoc = (e: MouseEvent) => { if (!menuRef.current) return; if (!menuRef.current.contains(e.target as Node)) setMenuOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setMenuOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return ()=>{ document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  },[]);

  const [src, setSrc] = useState<string>(pickEn(entry));
  const [tgt, setTgt] = useState<string>(pickZh(entry));
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");

  // 编辑区域点击外部自动收回
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
    try { await updateEntry(entry.id, { src, tgt }); onSaved(); onClose(); }
    catch(e:any){ setErr(e?.message || "保存失败"); }
    finally { setSaving(false); }
  }, [entry.id, src, tgt, onSaved, onClose]);

  const remove = useCallback(async ()=>{
    if (!confirm("确认删除该条目？")) return;
    try { await deleteEntry(entry.id); onDeleted(); }
    catch(e:any){ alert(e?.message || "删除失败"); }
  }, [entry.id, onDeleted]);

  return (
    <div className="rounded-lg border border-gray-200 overflow-hidden bg-white">
      {/* 只读卡片头 */}
      <div className="px-4 py-3">
        <div className="flex items-start gap-3">
          <div className="text-sm text-gray-500 w-8 shrink-0">#{index}</div>
          <div className="min-w-0 flex-1">
            <div className="text-[13px] text-gray-500 mb-1">
              <span className="mr-3">ID: {String(entry.id)}</span>
              <span>来源：{entry.source_name ?? ""}</span>
              <span className="ml-3">{(entry.created_at ?? "").replace?.("T"," ").slice?.(0,19)}</span>
            </div>
            <div className="font-medium text-gray-900 whitespace-pre-wrap">{pickEn(entry)}</div>
            <div className="text-gray-700 whitespace-pre-wrap mt-1">{pickZh(entry)}</div>
          </div>

          {/* 右上菜单 */}
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

      {/* 折叠编辑区域（显示在“下面”） */}
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

/* 工具栏标签组件 */
function ToolbarTab({ icon, label, active, onClick }: { icon: string; label: string; active: boolean; onClick: ()=>void; }) {
  return (
    <button
      className={cls(
        "relative px-3 py-3 flex items-center gap-2 text-[15px] border-b-2 -mb-px",
        active ? "border-rose-500 text-rose-600" : "border-transparent text-gray-700 hover:text-black hover:border-gray-200"
      )}
      onClick={onClick}
    >
      <span className="text-base">{icon}</span>
      <span>{label}</span>
    </button>
  );
}
