"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";

type Direction = "zh>en" | "en>zh";

type SplitMode =
  | "none"
  | "cn-punct"
  | "en-punct"
  | "regex";

type Entry = {
  text: string;
  translation?: string;
  direction: Direction;
  source_name?: string;
  source_id?: string | number;
  ts_iso: string;
};

type SourceItem = {
  id?: string | number;
  name?: string;
  source_name?: string;
} | string;

// ============ 可配置的 API（优先使用环境变量，不改代码即可切换） ============
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";
const SOURCES_ENDPOINT = process.env.NEXT_PUBLIC_SOURCES_ENDPOINT || "/sources";
const INSERT_ENDPOINT = process.env.NEXT_PUBLIC_INSERT_ENDPOINT || "/entries/batch";
const RENAME_ENDPOINT = process.env.NEXT_PUBLIC_RENAME_ENDPOINT || "/sources/rename";
const RECENT_ENDPOINT = process.env.NEXT_PUBLIC_RECENT_ENDPOINT || "/entries/recent";

// 简单的中英文标点正则
const CN_SPLIT_REGEX = /[。！？；：…]+\s*/g; // 中文句号、感叹号、问号、分号、冒号、省略号
const EN_SPLIT_REGEX = /[\.!?;:]+\s*/g;   // 英文 . ! ? ; :

function splitParagraph(input: string, mode: SplitMode, customRegex?: string): string[] {
  const text = (input || "").trim();
  if (!text) return [];
  if (mode === "none") return [text];

  if (mode === "cn-punct") {
    return smartSplit(text, CN_SPLIT_REGEX);
  }
  if (mode === "en-punct") {
    return smartSplit(text, EN_SPLIT_REGEX);
  }
  // regex
  try {
    const r = new RegExp(customRegex ?? "", "g");
    return smartSplit(text, r);
  } catch {
    // 自定义正则不合法则整段入库，避免破坏
    return [text];
  }
}

function smartSplit(text: string, re: RegExp): string[] {
  // 把分隔符当作边界，但不丢失分隔符（更接近人工句读）
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

function classNames(...xs: Array<string | false | null | undefined>) {
  return xs.filter(Boolean).join(" ");
}

// 兼容不同来源列表返回格式
function normalizeSources(data: any): { id?: string | number; name: string }[] {
  if (!data) return [];
  const arr = Array.isArray(data) ? data : [];
  return arr.map((x: SourceItem) => {
    if (typeof x === "string") return { name: x };
    const id = (x as any).id;
    // 优先 name，再退化 source_name
    const name = (x as any).name ?? (x as any).source_name ?? String(id ?? "");
    return { id, name };
  }).filter((s) => s.name);
}

// 简单语言计数
function langScore(text: string) {
  const zh = (text.match(/[\u4e00-\u9fff]/g) || []).length;
  const en = (text.match(/[A-Za-z]/g) || []).length;
  return { zh, en };
}

// 柔性读取 inserted 数量
async function readInsertedCount(resp: Response, fallback: number) {
  try {
    const data = await resp.json();
    // 常见三种：{inserted:n} | {count:n} | 直接数组
    if (typeof (data as any)?.inserted === "number") return (data as any).inserted;
    if (typeof (data as any)?.count === "number") return (data as any).count;
    if (Array.isArray(data)) return data.length;
  } catch { /* ignore */ }
  return fallback;
}

export default function InsertPage() {
  const [tab, setTab] = useState<"insert" | "preview" | "detect" | "rename" | "recent">("insert");

  const [direction, setDirection] = useState<Direction>("en>zh");
  const [splitMode, setSplitMode] = useState<SplitMode>("none");
  const [regexText, setRegexText] = useState<string>("[。\\.！？;；：,:、]+");

  const [enPara, setEnPara] = useState<string>("");
  const [zhPara, setZhPara] = useState<string>("");

  // Detection settings
  const [detectEnabled, setDetectEnabled] = useState<boolean>(true);
  const [detectMinLen, setDetectMinLen] = useState<number>(10);
  const [detectDominance, setDetectDominance] = useState<number>(2.0);

  // Source 选择：existing or New...
  const [existingSources, setExistingSources] = useState<{ id?: string | number; name: string }[]>([]);
  const [sourceQuery, setSourceQuery] = useState<string>("");
  const [sourceModeNew, setSourceModeNew] = useState<boolean>(true);
  const [newSourceName, setNewSourceName] = useState<string>("MyBatch");
  const [chosenSource, setChosenSource] = useState<{ id?: string | number; name: string } | null>(null);

  const [tsISO, setTsISO] = useState<string>(new Date().toISOString().slice(0,19));

  // 载入已有 source 列表（容错：即使失败也不影响 UI）
  useEffect(() => {
    fetch(API_BASE + SOURCES_ENDPOINT, { method: "GET" })
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((data) => setExistingSources(normalizeSources(data)))
      .catch(() => setExistingSources([]));
  }, []);

  // 依据方向，决定“源”段落是哪一侧
  const sourceParagraph = direction === "en>zh" ? enPara : zhPara;
  const targetParagraph = direction === "en>zh" ? zhPara : enPara;

  // 拆分结果
  const srcPieces = useMemo(
    () => splitParagraph(sourceParagraph, splitMode, regexText),
    [sourceParagraph, splitMode, regexText]
  );
  const trgPieces = useMemo(
    () => splitParagraph(targetParagraph, splitMode, regexText),
    [targetParagraph, splitMode, regexText]
  );

  const willInsertCount = Math.max(srcPieces.length, trgPieces.length);

  const warnMismatch =
    splitMode !== "none" &&
    srcPieces.length > 0 &&
    trgPieces.length > 0 &&
    srcPieces.length !== trgPieces.length;

  const finalSourceName = (sourceModeNew ? newSourceName : (chosenSource?.name ?? "")).trim();
  const finalSourceId = sourceModeNew ? undefined : chosenSource?.id;

  const entriesPreview: Entry[] = useMemo(() => {
    const out: Entry[] = [];
    for (let i = 0; i < willInsertCount; i++) {
      const text = (srcPieces[i] ?? "").trim();
      const translation = (trgPieces[i] ?? "").trim();
      if (!(text || translation)) continue;
      out.push({
        text: direction === "en>zh" ? text : translation || "",
        translation: direction === "en>zh" ? translation || "" : text,
        direction,
        source_name: finalSourceName || undefined,
        source_id: finalSourceId,
        ts_iso: tsISO,
      });
    }
    return out;
  }, [willInsertCount, srcPieces, trgPieces, direction, finalSourceName, finalSourceId, tsISO]);

  // 方向检测：在入库前做轻量检查（可关闭）
  const directionOk = useMemo(() => {
    if (!detectEnabled) return true;
    const s = sourceParagraph.trim();
    if (s.length < detectMinLen) return true;
    const { zh, en } = langScore(s);
    const want = direction === "en>zh" ? "en" : "zh";
    const ok = want === "en" ? en >= detectDominance * Math.max(1, zh) : zh >= detectDominance * Math.max(1, en);
    return ok;
  }, [detectEnabled, detectMinLen, detectDominance, sourceParagraph, direction]);

  const canSubmit =
    tab === "insert" &&
    willInsertCount > 0 &&
    Boolean(finalSourceName || finalSourceId) &&
    (Boolean(sourceParagraph.trim()) || Boolean(targetParagraph.trim())) &&
    directionOk;

  const [submitting, setSubmitting] = useState(false);
  const [submitMsg, setSubmitMsg] = useState<string>("");

  const handleInsert = useCallback(async () => {
    setSubmitting(true);
    setSubmitMsg("");
    try {
      const body = { items: entriesPreview };
      const resp = await fetch(API_BASE + INSERT_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const cnt = await readInsertedCount(resp, entriesPreview.length);
      setSubmitMsg(`成功插入 ${cnt} 条。`);
      setEnPara(""); setZhPara("");
    } catch (e: any) {
      setSubmitMsg(`插入失败：${e?.message || "网络/后端错误"}`);
    } finally {
      setSubmitting(false);
    }
  }, [entriesPreview]);

  const filteredSources = useMemo(() => {
    return [...existingSources]
      .sort((a,b)=>a.name.localeCompare(b.name))
      .filter(s => s.name.toLowerCase().includes(sourceQuery.toLowerCase()));
  }, [existingSources, sourceQuery]);

  // ======= 浮动（粘顶）控制条 =======
  const [elevated, setElevated] = useState(false);
  useEffect(() => {
    const onScroll = () => setElevated(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // ================= Rename 状态/行为 =================
  const [renameFrom, setRenameFrom] = useState<string>("");
  const [renameTo, setRenameTo] = useState<string>("");
  const [renameMsg, setRenameMsg] = useState<string>("");
  const [renamePreview, setRenamePreview] = useState<boolean>(true);

  const doRename = useCallback(async () => {
    setRenameMsg("");
    try {
      const payload = { from: renameFrom.trim(), to: renameTo.trim(), preview: renamePreview };
      const resp = await fetch(API_BASE + RENAME_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json().catch(() => ({}));
      const changed = (data?.changed ?? data?.updated ?? data?.count ?? 0) as number;
      setRenameMsg(renamePreview ? `预览：将影响 ${changed} 条。` : `完成：已更新 ${changed} 条。`);
    } catch (e: any) {
      setRenameMsg(`重命名失败：${e?.message || "网络/后端错误"}`);
    }
  }, [renameFrom, renameTo, renamePreview]);

  // ================= Recent 状态/行为 =================
  const [recentLimit, setRecentLimit] = useState<number>(20);
  const [recentData, setRecentData] = useState<any[]>([]);
  const [recentMsg, setRecentMsg] = useState<string>("");

  const loadRecent = useCallback(async () => {
    setRecentMsg("");
    try {
      const url = new URL(API_BASE + RECENT_ENDPOINT, window.location.href);
      url.searchParams.set("limit", String(recentLimit));
      const resp = await fetch(url.toString(), { method: "GET" });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      const arr = Array.isArray(data) ? data : (Array.isArray((data as any)?.items) ? (data as any).items : []);
      setRecentData(arr);
      setRecentMsg(`共返回 ${arr.length} 条。`);
    } catch (e: any) {
      setRecentMsg(`获取失败：${e?.message || "网络/后端错误"}`);
      setRecentData([]);
    }
  }, [recentLimit]);

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <h1 className="text-3xl font-semibold mb-4">Insert — Insert / Detection / Rename / Recent (API)</h1>

      {/* 粘顶控制条 */}
      <div
        className={classNames(
          "sticky top-0 z-30",
          "backdrop-blur bg-white/80 supports-[backdrop-filter]:bg-white/55",
          "border-b",
          elevated ? "shadow-sm" : "shadow-none"
        )}
      >
        <div className="flex gap-6 text-gray-700 items-center py-3">
          {[
            ["insert","Insert"],
            ["preview","Preview"],
            ["detect","Detection"],
            ["rename","Rename"],
            ["recent","Recent"],
          ].map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key as any)}
              className={classNames(
                "py-2 relative",
                tab === key ? "text-rose-600 font-medium" : "text-gray-600 hover:text-gray-800"
              )}
            >
              {label}
              {tab === key && <span className="absolute -bottom-[10px] left-0 right-0 h-[2px] bg-rose-500" />}
            </button>
          ))}

          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-gray-500">将要插入的条目数：</span>
            <input
              className="w-14 text-center rounded border border-gray-300 bg-gray-50 py-1"
              value={willInsertCount}
              readOnly
            />
            <button
              disabled={!canSubmit || submitting}
              onClick={handleInsert}
              className={classNames(
                "ml-2 rounded px-4 py-2 transition",
                canSubmit && !submitting ? "bg-rose-600 text-white hover:bg-rose-700" : "bg-gray-300 text-gray-600 cursor-not-allowed"
              )}
            >
              {submitting ? "插入中…" : "入库 / Insert"}
            </button>
          </div>
        </div>
      </div>

      {submitMsg && (
        <div className="mt-3 mb-4 rounded border border-gray-200 bg-yellow-50 px-4 py-2 text-sm text-gray-700">
          {submitMsg}
        </div>
      )}

      {/* 插入表单 */}
      {tab === "insert" && (
        <div className="space-y-6 pt-4">
          {/* Direction */}
          <div>
            <label className="block text-sm text-gray-600">本批次翻译方向 / Direction</label>
            <div className="mt-2 flex items-center gap-8">
              <label className="flex items-center gap-2">
                <input type="radio" name="dir" checked={direction === "zh>en"} onChange={() => setDirection("zh>en")} />
                <span>zh→en</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" name="dir" checked={direction === "en>zh"} onChange={() => setDirection("en>zh")} />
                <span>en→zh</span>
              </label>
            </div>
          </div>

          {/* Split Mode */}
          <div>
            <label className="block text-sm text-gray-600">拆分方式 / Split Mode</label>
            <select
              className="mt-2 w-full rounded border border-gray-300 px-3 py-2 bg-gray-50"
              value={splitMode}
              onChange={(e) => setSplitMode(e.target.value as SplitMode)}
            >
              <option value="none">不要拆分（整段入库）</option>
              <option value="cn-punct">按标点拆句（中文规则）</option>
              <option value="en-punct">按标点拆句（英文规则）</option>
              <option value="regex">按自定义分隔符（Regex）</option>
            </select>
            <div className="mt-2">
              <label className="block text-xs text-gray-500">分隔符正则（仅“自定义分隔符”生效）</label>
              <input
                className="mt-1 w-full rounded border border-gray-300 px-3 py-2"
                placeholder="[。 ！ ？ ； ： , : 、]+ 之类的"
                value={regexText}
                onChange={(e) => setRegexText(e.target.value)}
                disabled={splitMode !== "regex"}
              />
            </div>
            {warnMismatch && (
              <p className="mt-2 text-xs text-amber-600">
                预警：源文与译文的拆分数量不一致（{srcPieces.length} vs {trgPieces.length}），将按最长对齐并以空字符串填充短缺端。
              </p>
            )}
            {!directionOk && (
              <p className="mt-2 text-xs text-red-600">
                检测到源文与当前方向可能不符，请确认“翻译方向”是否正确，或在 Detection 中关闭自动检测。
              </p>
            )}
          </div>

          {/* 双栏输入 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm text-gray-600">English paragraph（Source）</label>
              <textarea className="mt-2 w-full h-56 rounded border border-gray-300 px-3 py-2 bg-gray-50" value={enPara} onChange={(e) => setEnPara(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm text-gray-600">中文段落（译文，可选）</label>
              <textarea className="mt-2 w-full h-56 rounded border border-gray-300 px-3 py-2 bg-gray-50" value={zhPara} onChange={(e) => setZhPara(e.target.value)} />
            </div>
          </div>

          {/* Source Name 选择 */}
          <div>
            <label className="block text-sm text-gray-600">统一出处 / Source Name（可输入以搜索已有）</label>

            <div className="mt-2 flex items-center gap-3">
              <button
                type="button"
                className={classNames("rounded px-3 py-2 text-sm border", sourceModeNew ? "bg-rose-50 border-rose-300 text-rose-700" : "bg-gray-50 border-gray-300 text-gray-700")}
                onClick={() => setSourceModeNew(true)}
                title="新增一个来源名称"
              >
                ＋ New…
              </button>
              <button
                type="button"
                className={classNames("rounded px-3 py-2 text-sm border", !sourceModeNew ? "bg-rose-50 border-rose-300 text-rose-700" : "bg-gray-50 border-gray-300 text-gray-700")}
                onClick={() => setSourceModeNew(false)}
                title="从既有来源中选择"
              >
                从列表选择
              </button>
            </div>

            {sourceModeNew ? (
              <div className="mt-3">
                <label className="block text-xs text-gray-500">New source name</label>
                <input className="mt-1 w-full rounded border border-gray-300 px-3 py-2" placeholder="如：The Economist_2025-10-18" value={newSourceName} onChange={(e) => setNewSourceName(e.target.value)} />
              </div>
            ) : (
              <div className="mt-3">
                <label className="block text-xs text-gray-500">搜索并选择已有来源（按字母排序）</label>
                <input className="mt-1 w-full rounded border border-gray-300 px-3 py-2" placeholder="输入关键字过滤…" value={sourceQuery} onChange={(e) => setSourceQuery(e.target.value)} />
                <div className="mt-2 max-h-40 overflow-auto rounded border border-gray-200 bg-white">
                  {filteredSources.map((s) => (
                    <button
                      key={String(s.id ?? s.name)}
                      type="button"
                      className={classNames("w-full text-left px-3 py-2 hover:bg-rose-50", chosenSource?.name === s.name && "bg-rose-100")}
                      onClick={() => setChosenSource(s)}
                    >
                      {s.name}
                    </button>
                  ))}
                  {filteredSources.length === 0 && <div className="px-3 py-2 text-sm text-gray-500">无匹配项</div>}
                </div>
              </div>
            )}
          </div>

          {/* Timestamp */}
          <div>
            <label className="block text-sm text-gray-600">统一时间 / Timestamp (ISO)</label>
            <input className="mt-2 w-full rounded border border-gray-300 px-3 py-2" value={tsISO} onChange={(e) => setTsISO(e.target.value)} />
          </div>
        </div>
      )}

      {/* 预览 */}
      {tab === "preview" && (
        <div className="space-y-3 pt-4">
          <div className="text-sm text-gray-600">预览即将入库的结构（最多显示前 50 条）</div>
          <div className="rounded border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left">#</th>
                  <th className="px-3 py-2 text-left">text</th>
                  <th className="px-3 py-2 text-left">translation</th>
                  <th className="px-3 py-2 text-left">direction</th>
                  <th className="px-3 py-2 text-left">source_id</th>
                  <th className="px-3 py-2 text-left">source_name</th>
                  <th className="px-3 py-2 text-left">ts_iso</th>
                </tr>
              </thead>
              <tbody>
                {entriesPreview.slice(0, 50).map((e, i) => (
                  <tr key={i} className={i % 2 ? "bg-white" : "bg-gray-50"}>
                    <td className="px-3 py-2">{i + 1}</td>
                    <td className="px-3 py-2 whitespace-pre-wrap">{e.text}</td>
                    <td className="px-3 py-2 whitespace-pre-wrap">{e.translation}</td>
                    <td className="px-3 py-2">{e.direction}</td>
                    <td className="px-3 py-2">{String(e.source_id ?? "")}</td>
                    <td className="px-3 py-2">{e.source_name}</td>
                    <td className="px-3 py-2">{e.ts_iso}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Detection */}
      {tab === "detect" && (
        <div className="pt-4 space-y-4 text-sm text-gray-700">
          <div className="rounded border p-4 bg-gray-50">
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={detectEnabled} onChange={(e)=>setDetectEnabled(e.target.checked)} />
              <span>启用语言方向检测（入库前校验源文大致符合所选方向）</span>
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-3">
              <div>
                <label className="block text-gray-500 mb-1">最小检测长度</label>
                <input type="number" min={0} className="w-full rounded border px-3 py-2" value={detectMinLen} onChange={(e)=>setDetectMinLen(parseInt(e.target.value||"0"))} />
              </div>
              <div>
                <label className="block text-gray-500 mb-1">主导比</label>
                <input type="number" step="0.1" min={1} className="w-full rounded border px-3 py-2" value={detectDominance} onChange={(e)=>setDetectDominance(parseFloat(e.target.value||"1"))} />
              </div>
              <div className="flex items-end">
                <p className="text-xs text-gray-500">当中文（或英文）字符数 ≥ 主导比 × 另一方时判定方向正确。</p>
              </div>
            </div>
          </div>

          <div className="rounded border p-4">
            <div className="font-medium mb-2">即时检测（取当前“源文”段落示例）</div>
            <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto">{JSON.stringify({ want: direction === "en>zh" ? "英文" : "中文", sampleLength: sourceParagraph.length, score: langScore(sourceParagraph) }, null, 2)}</pre>
            <div className={classNames("mt-2 text-sm", directionOk ? "text-green-700" : "text-red-700")}>
              {directionOk ? "✓ 通过：当前样本与所选方向大致一致" : "× 警告：当前样本可能与所选方向不符"}
            </div>
          </div>
        </div>
      )}

      {/* Rename */}
      {tab === "rename" && (
        <div className="pt-4 space-y-4">
          <div className="rounded border p-4 bg-gray-50">
            <div className="text-sm text-gray-700 mb-3">从已有来源中选择要改名的“旧名称”，并填写“新名称”。默认先做预览，不会改动数据库。</div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-gray-600 mb-1">旧名称（from）</label>
                <input list="source-list" className="w-full rounded border px-3 py-2" value={renameFrom} onChange={(e)=>setRenameFrom(e.target.value)} placeholder="选择或输入…" />
                <datalist id="source-list">
                  {existingSources.map(s => <option key={String(s.id ?? s.name)} value={s.name} />)}
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
              <button
                onClick={doRename}
                disabled={!renameFrom.trim() || !renameTo.trim()}
                className={classNames("ml-auto rounded px-4 py-2", (!renameFrom.trim() || !renameTo.trim()) ? "bg-gray-300 text-gray-600" : "bg-rose-600 text-white hover:bg-rose-700")}
              >
                {renamePreview ? "预览影响范围" : "执行重命名"}
              </button>
            </div>
            {renameMsg && <div className="mt-3 text-sm text-gray-700">{renameMsg}</div>}
          </div>
        </div>
      )}

      {/* Recent */}
      {tab === "recent" && (
        <div className="pt-4 space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-700">显示最近</label>
            <input type="number" min={1} className="w-24 rounded border px-3 py-2" value={recentLimit} onChange={(e)=>setRecentLimit(parseInt(e.target.value||"1"))} />
            <span className="text-sm text-gray-700">条</span>
            <button onClick={loadRecent} className="ml-2 rounded px-4 py-2 bg-rose-600 text-white hover:bg-rose-700">刷新</button>
            {recentMsg && <span className="text-sm text-gray-600 ml-3">{recentMsg}</span>}
          </div>
          <div className="rounded border overflow-hidden">
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
                    <td className="px-3 py-2 whitespace-pre-wrap">{String((e?.text ?? e?.src ?? ""))}</td>
                    <td className="px-3 py-2 whitespace-pre-wrap">{String((e?.translation ?? e?.tgt ?? ""))}</td>
                    <td className="px-3 py-2">{String((e?.source_name ?? e?.source ?? ""))}</td>
                    <td className="px-3 py-2">{String((e?.ts_iso ?? e?.created_at ?? ""))}</td>
                  </tr>
                ))}
                {recentData.length === 0 && (
                  <tr><td className="px-3 py-6 text-center text-gray-500" colSpan={5}>暂无数据</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
