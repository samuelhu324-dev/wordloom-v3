"use client";
import React, { useEffect, useMemo, useState, useCallback } from "react";
import { listSources, renameSource } from "@/modules/loom/services/sources";
import { batchInsert, listRecent } from "@/modules/loom/services/entries";
import Combobox from "../shared/Combobox";

type Direction = "zh>en" | "en>zh";
type SplitMode = "none" | "cn-punct" | "en-punct" | "regex";

const CN_SPLIT_REGEX = /[。！？；：…]+\s*/g;
const EN_SPLIT_REGEX = /[\.!?;:]+\s*/g;

function smartSplit(text: string, re: RegExp): string[] {
  const parts: string[] = [];
  let start = 0;
  let m: RegExpExecArray | null;
  re.lastIndex = 0;
  while ((m = re.exec(text))) {
    const end = re.lastIndex;
    const chunk = text.slice(start, end).trim();
    if (chunk) parts.push(chunk);
    start = end;
  }
  const tail = text.slice(start).trim();
  if (tail) parts.push(tail);
  return parts;
}

function splitParagraph(input: string, mode: SplitMode, customRegex?: string): string[] {
  const text = (input || "").trim();
  if (!text) return [];
  if (mode === "none") return [text];
  if (mode === "cn-punct") return smartSplit(text, CN_SPLIT_REGEX);
  if (mode === "en-punct") return smartSplit(text, EN_SPLIT_REGEX);
  try { return smartSplit(text, new RegExp(customRegex ?? "", "g")); } catch { return [text]; }
}

function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}
function langScore(text: string){
  const zh = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const en = (text.match(/[A-Za-z]/g) || []).length;
  return { zh, en };
}

export default function InsertPanel(){
  const [direction, setDirection] = useState<Direction>("en>zh");
  const [splitMode, setSplitMode] = useState<SplitMode>("none");
  const [regexText, setRegexText] = useState<string>("[。\\.！？;；：,:、]+");
  const [enPara, setEnPara] = useState<string>("");
  const [zhPara, setZhPara] = useState<string>("");

  const [sources, setSources] = useState<{id?: string|number; name: string}[]>([]);
  const [sourceModeNew, setSourceModeNew] = useState(true);
  const [sourceQuery, setSourceQuery] = useState("");
  const [newSourceName, setNewSourceName] = useState("MyBatch");
  const [chosenSource, setChosenSource] = useState<{id?: string|number; name: string} | null>(null);
  const [tsISO, setTsISO] = useState(new Date().toISOString().slice(0,19));

  const [detectEnabled, setDetectEnabled] = useState(true);
  const [detectMinLen, setDetectMinLen] = useState(10);
  const [detectDominance, setDetectDominance] = useState(2.0);

  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState("");

  const [renameFrom, setRenameFrom] = useState("");
  const [renameTo, setRenameTo] = useState("");
  const [renamePreview, setRenamePreview] = useState(true);
  const [renameMsg, setRenameMsg] = useState("");

  const [recentLimit, setRecentLimit] = useState(20);
  const [recentData, setRecentData] = useState<any[]>([]);
  const [recentMsg, setRecentMsg] = useState("");

  useEffect(()=>{
    listSources()
      .then(arr => setSources(arr))
      .catch(()=>setSources([]));
  }, []);

  const sourceParagraph = direction === "en>zh" ? enPara : zhPara;
  const targetParagraph = direction === "en>zh" ? zhPara : enPara;

  const srcPieces = useMemo(()=> splitParagraph(sourceParagraph, splitMode, regexText), [sourceParagraph, splitMode, regexText]);
  const trgPieces = useMemo(()=> splitParagraph(targetParagraph, splitMode, regexText), [targetParagraph, splitMode, regexText]);
  const willInsertCount = Math.max(srcPieces.length, trgPieces.length);
  const warnMismatch = splitMode !== "none" && srcPieces.length>0 && trgPieces.length>0 && srcPieces.length!==trgPieces.length;

  const finalSourceName = (sourceModeNew ? newSourceName : (chosenSource?.name ?? "")).trim();
  const finalSourceId = sourceModeNew ? undefined : chosenSource?.id;

  const entriesPreview = useMemo(()=>{
    const out: any[] = [];
    for (let i=0;i<willInsertCount;i++){
      const t = (srcPieces[i] ?? "").trim();
      const tr = (trgPieces[i] ?? "").trim();
      if (!(t || tr)) continue;
      out.push({
        text: direction === "en>zh" ? t : tr || "",
        translation: direction === "en>zh" ? tr || "" : t,
        direction,
        source_name: finalSourceName || undefined,
        source_id: finalSourceId,
        ts_iso: tsISO,
      });
    }
    return out;
  }, [willInsertCount, srcPieces, trgPieces, direction, finalSourceName, finalSourceId, tsISO]);

  const directionOk = useMemo(()=>{
    if (!detectEnabled) return true;
    const s = sourceParagraph.trim();
    if (s.length < detectMinLen) return true;
    const { zh, en } = langScore(s);
    const want = direction === "en>zh" ? "en" : "zh";
    return want==="en" ? en >= detectDominance * Math.max(1, zh) : zh >= detectDominance * Math.max(1, en);
  }, [detectEnabled, detectMinLen, detectDominance, sourceParagraph, direction]);

  const canSubmit = willInsertCount>0 && Boolean(finalSourceName || finalSourceId)
    && (Boolean(sourceParagraph.trim()) || Boolean(targetParagraph.trim())) && directionOk;

  const handleInsert = useCallback(async ()=>{
    setSubmitting(true); setSubmitMsg("");
    try {
      const r = await batchInsert(entriesPreview);
      if (!r.ok) throw new Error("HTTP " + r.status);
      setSubmitMsg(`成功插入 ${entriesPreview.length} 条。`);
      setEnPara(""); setZhPara("");
    } catch(e:any){
      setSubmitMsg(`插入失败：${e?.message || "网络/后端错误"}`);
    } finally { setSubmitting(false); }
  }, [entriesPreview]);

  const doRename = useCallback(async ()=>{
    setRenameMsg("");
    try {
      const data = await renameSource(renameFrom.trim(), renameTo.trim(), renamePreview);
      const changed = (data?.changed ?? data?.updated ?? data?.count ?? 0) as number;
      setRenameMsg(renamePreview ? `预览：将影响 ${changed} 条。` : `完成：已更新 ${changed} 条。`);
    } catch(e:any){
      setRenameMsg(`重命名失败：${e?.message || "网络/后端错误"}`);
    }
  }, [renameFrom, renameTo, renamePreview]);

  const filteredSources = useMemo(()=>{
    return [...sources]
      .filter(s => !!s?.name)
      .sort((a,b)=> (a.name||"").localeCompare(b.name||""))
      .filter(s=> (s.name||"").toLowerCase().includes(sourceQuery.toLowerCase()));
  }, [sources, sourceQuery]);

  const loadRecent = useCallback(async ()=>{
    setRecentMsg("");
    try {
      const arr = await listRecent(recentLimit);
      setRecentData(arr); setRecentMsg(`共返回 ${arr.length} 条。`);
    } catch(e:any){
      setRecentMsg(`获取失败：${e?.message || "网络/后端错误"}`);
      setRecentData([]);
    }
  }, [recentLimit]);

  // 生成 datalist 的唯一且稳定的选项（去空、去重）
  const datalistOptions = useMemo(()=>{
    const m = new Map<string, {id?: string|number; name: string}>();
    for (const s of sources) {
      if (!s || !s.name) continue;
      if (!m.has(s.name)) m.set(s.name, s);
    }
    return Array.from(m.values());
  }, [sources]);

  return (
    <div className="space-y-6 pt-2">
      <div>
        <label className="block text-sm text-gray-600">本批次翻译方向 / Direction</label>
        <div className="mt-2 flex items-center gap-8">
          <label className="flex items-center gap-2">
            <input type="radio" name="dir" checked={direction==="zh>en"} onChange={()=>setDirection("zh>en")} />
            <span>zh→en</span>
          </label>
          <label className="flex items-center gap-2">
            <input type="radio" name="dir" checked={direction==="en>zh"} onChange={()=>setDirection("en>zh")} />
            <span>en→zh</span>
          </label>
        </div>
      </div>

      <div>
        <label className="block text-sm text-gray-600">拆分方式 / Split Mode</label>
        <select className="mt-2 w-full rounded border px-3 py-2 bg-gray-50" value={splitMode} onChange={(e)=>setSplitMode(e.target.value as SplitMode)}>
          <option value="none">不要拆分（整段入库）</option>
          <option value="cn-punct">按标点拆句（中文规则）</option>
          <option value="en-punct">按标点拆句（英文规则）</option>
          <option value="regex">按自定义分隔符（Regex）</option>
        </select>
        <div className="mt-2">
          <label className="block text-xs text-gray-500">分隔符正则（仅“自定义分隔符”生效）</label>
          <input className="mt-1 w-full rounded border px-3 py-2" placeholder="[。 ！ ？ ； ： , : 、]+ 之类的" value={regexText} onChange={(e)=>setRegexText(e.target.value)} disabled={splitMode!=="regex"} />
        </div>
        {warnMismatch && <p className="mt-2 text-xs text-amber-600">预警：源文与译文的拆分数量不一致（{srcPieces.length} vs {trgPieces.length}）</p>}
        {!directionOk && <p className="mt-2 text-xs text-red-600">检测到源文与当前方向可能不符，确认“翻译方向”或关闭检测。</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm text-gray-600">English paragraph（Source）</label>
          <textarea className="mt-2 w-full h-48 rounded border px-3 py-2 bg-gray-50" value={enPara} onChange={(e)=>setEnPara(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm text-gray-600">中文段落（译文，可选）</label>
          <textarea className="mt-2 w-full h-48 rounded border px-3 py-2 bg-gray-50" value={zhPara} onChange={(e)=>setZhPara(e.target.value)} />
        </div>
      </div>

      <div>
        <label className="block text-sm text-gray-600">统一出处 / Source Name</label>
        <div className="mt-2 flex items-center gap-3">
          <button type="button" className={`rounded px-3 py-2 text-sm border ${sourceModeNew ? "bg-rose-50 border-rose-300 text-rose-700":"bg-gray-50 border-gray-300 text-gray-700"}`} onClick={()=>setSourceModeNew(true)}>＋ New…</button>
          <button type="button" className={`rounded px-3 py-2 text-sm border ${!sourceModeNew ? "bg-rose-50 border-rose-300 text-rose-700":"bg-gray-50 border-gray-300 text-gray-700"}`} onClick={()=>setSourceModeNew(false)}>从列表选择</button>
        </div>
        {sourceModeNew ? (
          <div className="mt-3">
            <label className="block text-xs text-gray-500">New source name</label>
            <input className="mt-1 w-full rounded border px-3 py-2" value={newSourceName} onChange={(e)=>setNewSourceName(e.target.value)} />
          </div>
        ) : (
          <div className="mt-3">
            <label className="block text-xs text-gray-500">搜索并选择已有来源（按字母排序）</label>
            <input className="mt-1 w-full rounded border px-3 py-2" placeholder="输入关键字过滤…" value={sourceQuery} onChange={(e)=>setSourceQuery(e.target.value)} />
            <div className="mt-2 max-h-40 overflow-auto rounded border border-gray-200 bg-white">
              {filteredSources.map((s)=>(
                <button
                  key={`${s.id ?? "N"}:${s.name}`}
                  type="button"
                  className={`w-full text-left px-3 py-2 hover:bg-rose-50 ${chosenSource?.name===s.name?"bg-rose-100":""}`}
                  onClick={()=>setChosenSource(s)}
                >
                  {s.name}
                </button>
              ))}
              {filteredSources.length===0 && <div className="px-3 py-2 text-sm text-gray-500">无匹配项</div>}
            </div>
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm text-gray-600">统一时间 / Timestamp (ISO)</label>
        <input className="mt-2 w-full rounded border px-3 py-2" value={tsISO} onChange={(e)=>setTsISO(e.target.value)} />
      </div>

      <div className="sticky top-0 z-30 backdrop-blur bg-white/80 border-y py-2">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">将要插入的条目数：</span>
          <input className="w-14 text-center rounded border bg-gray-50 py-1" value={willInsertCount} readOnly />
          <button disabled={!canSubmit || submitting} onClick={handleInsert}
            className={`ml-2 rounded px-4 py-2 transition ${canSubmit && !submitting ? "bg-rose-600 text-white hover:bg-rose-700":"bg-gray-300 text-gray-600 cursor-not-allowed"}`}>
            {submitting ? "插入中…" : "入库 / Insert"}
          </button>
          {submitMsg && <span className="text-sm text-gray-700 ml-3">{submitMsg}</span>}
        </div>
      </div>

      <div className="wl-card rounded p-4">
        <div className="text-sm text-gray-700 mb-3">来源重命名（支持预览）</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-600 mb-1">旧名称（from）</label>
            <input list="source-list" className="w-full rounded border px-3 py-2" value={renameFrom} onChange={(e)=>setRenameFrom(e.target.value)} placeholder="选择或输入…" />
            <datalist id="source-list">
              {datalistOptions.map((s, idx) => (
                <option key={`${s.id ?? "N"}:${s.name}:${idx}`} value={s.name} />
              ))}
            </datalist>
          </div>
          <div>
            <label className="block text-sm text-gray-600 mb-1">新名称（to）</label>
            <input className="w-full rounded border px-3 py-2" value={renameTo} onChange={(e)=>setRenameTo(e.target.value)} placeholder="输入要替换成的名称…" />
          </div>
        </div>
        <div className="flex items-center gap-3 mt-3 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={renamePreview} onChange={(e)=>setRenamePreview(e.target.checked)} />
            <span>仅预览（不落库）</span>
          </label>
          <button onClick={doRename} disabled={!renameFrom.trim() || !renameTo.trim()}
            className={`ml-auto rounded px-4 py-2 ${(!renameFrom.trim() || !renameTo.trim()) ? "bg-gray-300 text-gray-600":"bg-rose-600 text-white hover:bg-rose-700"}`}>
            {renamePreview ? "预览影响范围" : "执行重命名"}
          </button>
          {renameMsg && <span className="text-sm text-gray-700 ml-3">{renameMsg}</span>}
        </div>
      </div>

      <div className="wl-card rounded p-4">
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-700">显示最近</label>
          <input type="number" min={1} className="w-24 rounded border px-3 py-2" value={recentLimit} onChange={(e)=>setRecentLimit(parseInt(e.target.value||"1"))} />
          <span className="text-sm text-gray-700">条</span>
          <button onClick={loadRecent} className="ml-2 rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">刷新</button>
          {recentMsg && <span className="text-sm text-gray-600 ml-3">{recentMsg}</span>}
        </div>
        <div className="mt-3 rounded border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left">#</th>
                <th className="px-3 py-2 text-left">text</th>
                <th className="px-3 py-2 text-left">translation</th>
                <th className="px-3 py-2 text-left">source</th>
                <th className="px-3 py-2 text-left">ts_iso</th>
              </tr>
            </thead>
            <tbody>
              {recentData.map((e, i) => (
                <tr key={i} className={i % 2 ? "bg-white" : "bg-gray-50"}>
                  <td className="px-3 py-2">{i + 1}</td>
                  <td className="px-3 py-2 whitespace-pre-wrap">{String(e?.text ?? "")}</td>
                  <td className="px-3 py-2 whitespace-pre-wrap">{String(e?.translation ?? "")}</td>
                  <td className="px-3 py-2">{String(e?.source_name ?? "")}</td>
                  <td className="px-3 py-2">{String(e?.created_at ?? "")}</td>
                </tr>
              ))}
              {recentData.length===0 && <tr><td className="px-3 py-6 text-center text-gray-500" colSpan={5}>暂无数据</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
