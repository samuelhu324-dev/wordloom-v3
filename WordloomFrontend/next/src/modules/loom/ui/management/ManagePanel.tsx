"use client";
import { useEffect, useState, useCallback, useMemo } from "react";
import type { EntryItem } from "@/modules/loom/services/entries";
import { searchEntries, updateEntry, deleteEntry, listRecent } from "@/modules/loom/services/entries";
import { listSources } from "@/modules/loom/services/sources";
import Combobox from "@/modules/loom/ui/shared/Combobox";

/** 兼容字段挑选：从多个键里选第一个有值的 */
const pick = (...xs: any[]) => {
  for (const v of xs) {
    if (v !== undefined && v !== null) {
      const s = typeof v === "string" ? v : String(v);
      if (s.trim() !== "") return s;
    }
  }
  return "";
};

/* ----------------------- 小卡片（含编辑/保存/删除） ----------------------- */
function EntryCard({
  item,
  onChanged,
}: {
  item: EntryItem;
  onChanged?: () => void;
}) {
  const [editing, setEditing] = useState(false);

  const readSrc = () => pick(item.src_text, item.src, (item as any).text, (item as any).left);
  const readTgt = () => pick(item.tgt_text, item.tgt, (item as any).translation, (item as any).right);

  const [src, setSrc] = useState<string>(readSrc());
  const [tgt, setTgt] = useState<string>(readTgt());
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    setSrc(readSrc());
    setTgt(readTgt());
    setEditing(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [item.id, item.src_text, item.tgt_text, (item as any).src, (item as any).tgt, (item as any).text, (item as any).translation, (item as any).left, (item as any).right]);

  async function onSave() {
    setSaving(true);
    setMsg("");
    try {
      const prevSrc = readSrc();
      const prevTgt = readTgt();
      const patch: Record<string, any> = {};
      if (src !== prevSrc) { patch.src = src; }
      if (tgt !== prevTgt) { patch.tgt = tgt; }
      if (Object.keys(patch).length === 0) { setEditing(false); return; }
      await updateEntry(item.id, patch as any);
      setMsg("已保存");
      onChanged?.();
      setEditing(false);
    } catch (e: any) {
      setMsg(`保存失败：${e?.message || "网络/后端错误"}`);
    } finally {
      setSaving(false);
      setTimeout(() => setMsg(""), 2200);
    }
  }

  async function onDelete() {
    if (!confirm(`确定删除 #${item.id} ？`)) return;
    try {
      await deleteEntry(item.id);
      onChanged?.();
    } catch (e: any) {
      alert(`删除失败：${e?.message || "网络/后端错误"}`);
    }
  }

  return (
    <div className="rounded-2xl bg-indigo-50/50 p-4 border border-indigo-100">
      <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
        <div className="flex items-center gap-4">
          <span>#{item.id}</span>
          <span>来源：{(item as any).source_name ?? (item as any).source ?? "—"}</span>
          <span>{(item as any).created_at ?? (item as any).create_time ?? ""}</span>
        </div>
        <div className="flex items-center gap-2">
          {!editing ? (
            <button
              className="px-3 py-1 rounded bg-indigo-600 text-white"
              onClick={() => setEditing(true)}
            >
              编辑
            </button>
          ) : (
            <>
              <button
                className="px-3 py-1 rounded bg-gray-200"
                onClick={() => {
                  setEditing(false);
                  setSrc(readSrc());
                  setTgt(readTgt());
                }}
              >
                取消
              </button>
              <button
                className="px-3 py-1 rounded bg-rose-600 text-white disabled:opacity-60"
                disabled={saving}
                onClick={onSave}
              >
                {saving ? "保存中…" : "保存"}
              </button>
            </>
          )}
          <button className="px-3 py-1 rounded bg-gray-100" onClick={onDelete}>
            删除
          </button>
        </div>
      </div>

      {!editing ? (
        <div className="space-y-2">
          <div data-role="entry-src" className="break-words whitespace-pre-wrap text-gray-900">
            {readSrc()}
          </div>
          <div data-role="entry-tgt" className="break-words whitespace-pre-wrap text-gray-700">
            {readTgt()}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <textarea
            className="w-full h-28 rounded border p-2 bg-white"
            value={src}
            onChange={(e) => setSrc(e.target.value)}
          />
          <textarea
            className="w-full h-28 rounded border p-2 bg-white"
            value={tgt}
            onChange={(e) => setTgt(e.target.value)}
          />
        </div>
      )}

      {msg && <div className="mt-2 text-xs text-gray-600">{msg}</div>}
    </div>
  );
}

/* ------------------------------ 主面板 ------------------------------ */
export default function ManagePanel() {
  // 查询条件
  const [keyword, setKeyword] = useState("");
  const [sourceName, setSourceName] = useState("");
  const [order, setOrder] = useState<"desc" | "asc">("desc");
  const [pageSize, setPageSize] = useState(10);
  const [offset, setOffset] = useState(0);

  // 数据
  const [items, setItems] = useState<EntryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  // 来源列表（给 Combobox）
  const [sources, setSources] = useState<{ id?: number | string; name: string }[]>([]);

  // 初始化加载来源
  useEffect(() => {
    listSources()
      .then((xs) => setSources(xs))
      .catch(() => setSources([]));
  }, []);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const { items, total } = await searchEntries({
        q: keyword.trim() || undefined,
        source_name: sourceName.trim() || undefined,
        limit: pageSize,
        offset,
      });
      setItems(order === "desc" ? items : [...items].reverse());
      setTotal(total);
    } catch (e: any) {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [keyword, sourceName, pageSize, offset, order]);

  useEffect(() => { reload(); }, [reload]);

  const onSearchClick = () => {
    setOffset(0);
    reload();
  };
  const onChanged = () => { reload(); };

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);
  const curPage = useMemo(() => Math.floor(offset / pageSize) + 1, [offset, pageSize]);

  return (
    <div className="space-y-4">
      {/* 条件区 */}
      <div className="grid grid-cols-1 md:grid-cols-[1fr_auto_auto_auto] gap-3 items-center">
        <input
          className="rounded border px-3 py-2"
          placeholder="关键词（可留空，仅按来源查找）"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onSearchClick()}
        />
        <select
          className="rounded border px-3 py-2"
          value={order}
          onChange={(e) => setOrder(e.target.value as "asc" | "desc")}
        >
          <option value="desc">倒序（新 → 旧）</option>
          <option value="asc">正序（旧 → 新）</option>
        </select>
        <button className="rounded bg-indigo-600 text-white px-4 py-2" onClick={onSearchClick}>搜索</button>
        <div className="text-right text-sm text-gray-600">
          共 {total} 条 每页{" "}
          <select
            className="border rounded px-2 py-1"
            value={pageSize}
            onChange={(e) => {
              setPageSize(parseInt(e.target.value, 10));
              setOffset(0);
            }}
          >
            {[10, 20, 50].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </div>
      </div>

      {/* 来源筛选 */}
      <div>
        <div className="text-sm text-gray-700 mb-1">来源</div>
        <Combobox
          value={sourceName}
          onChange={(name: string) => { setSourceName(name); setOffset(0); }}
          options={sources}
          placeholder="选择一个来源（可输入过滤）"
        />
      </div>

      {/* 列表 */}
      {loading ? (
        <div className="mt-4 text-sm text-gray-600">加载中…</div>
      ) : (
        <div className="mt-2 space-y-4">
          {items.map((it) => <EntryCard key={it.id} item={it} onChanged={onChanged} />)}
          {items.length === 0 && <div className="text-sm text-gray-500">没有匹配的结果</div>}
        </div>
      )}

      {/* 分页 */}
      <div className="flex items-center justify-between py-4">
        <div className="text-sm text-gray-600">第 {curPage}/{totalPages} 页</div>
        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded border" disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - pageSize))}>上一页</button>
          <button className="px-3 py-1 rounded border" disabled={offset + pageSize >= total} onClick={() => setOffset((o) => (o + pageSize < total ? o + pageSize : o))}>下一页</button>
        </div>
      </div>
    </div>
  );
}

