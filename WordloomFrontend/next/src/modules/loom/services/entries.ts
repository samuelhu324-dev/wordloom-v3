// src/modules/loom/services/entries.ts
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/common";

/** —— 数据类型 —— */
type RawEntry = {
  id: number;
  // 后端新版键
  src?: string;
  tgt?: string;
  // 旧版兼容键
  src_text?: string;
  tgt_text?: string;
  source_name?: string | null;
  created_at?: string | null;
};

export type EntryItem = RawEntry & {
  // 统一后的字段：UI 可直接读这两个
  src_text: string;
  tgt_text: string;
  // 额外别名，兼容旧 UI 写法
  text: string;
  translation: string;
};

async function getJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, {
    ...init,
    headers: {
      accept: "application/json",
      "content-type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return (await r.json()) as T;
}

// 把后端 src/tgt 映射为 src_text/tgt_text，并补出 text/translation 两个别名
const normalize = (e: RawEntry): EntryItem => {
  const src_text = (e.src_text ?? e.src ?? "") as string;
  const tgt_text = (e.tgt_text ?? e.tgt ?? "") as string;
  return {
    ...e,
    src_text,
    tgt_text,
    text: src_text,          // 兼容旧 UI：把“原文”映射到 text
    translation: tgt_text,   // 兼容旧 UI：把“译文”映射到 translation
  };
};

/** —— 查询 —— */
export async function searchEntries(params: {
  q?: string;
  source_name?: string;
  limit?: number;
  offset?: number;
} = {}) {
  const { q, source_name, limit = 20, offset = 0 } = params;
  const usp = new URLSearchParams();
  if (q) usp.set("q", q);
  if (source_name) usp.set("source_name", source_name);
  usp.set("limit", String(limit));
  usp.set("offset", String(offset));

  const data = await getJSON<{ items: RawEntry[]; total: number }>(
    `${API_BASE}/entries/search?${usp.toString()}`
  );
  return { items: data.items.map(normalize), total: data.total };
}

export async function listRecent(n = 20): Promise<EntryItem[]> {
  const { items } = await searchEntries({ limit: n, offset: 0 });
  return items;
}

/** —— 新增（批量）—— 优先 /entries/batch，降级逐条 POST /entries */
export async function batchInsert(items: Array<{
  text: string;
  translation?: string;
  direction: "en>zh" | "zh>en";
  source_name?: string;
  source_id?: number | string;
  ts_iso?: string;
}>) {
  // 先尝试批量端点
  try {
    const r = await fetch(`${API_BASE}/entries/batch`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify({ items }),
    });
    if (r.ok || r.status === 207) return r;
    if (r.status !== 404 && r.status !== 405)
      throw new Error(`${r.status} ${r.statusText}`);
  } catch { /* 降级 */ }

  // 再降级逐条
  let ok = true;
  for (const it of items) {
    const isEnToZh = it.direction === "en>zh";
    const payload = {
      src: isEnToZh ? it.text : it.translation ?? "",
      tgt: isEnToZh ? it.translation ?? "" : it.text,
      source_name: it.source_name,
      created_at: it.ts_iso,
    };
    const r = await fetch(`${API_BASE}/entries`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(payload),
    });
    if (!r.ok) ok = false;
  }
  return new Response(null, { status: ok ? 200 : 207 });
}

/** —— 单条更新 —— 优先 PATCH /entries/{id}，兼容旧 /entries/update */
export async function updateEntry(
  id: number,
  patch: { src?: string; tgt?: string; source_name?: string }
) {
  // 新式：PATCH /entries/{id}
  try {
    const r = await fetch(`${API_BASE}/entries/${id}`, {
      method: "PATCH",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(patch),
    });
    if (r.ok) return r;
    if (r.status !== 404 && r.status !== 405)
      throw new Error(`${r.status} ${r.statusText}`);
  } catch { /* 走旧式 */ }

  // 旧式：POST /entries/update
  return fetch(`${API_BASE}/entries/update`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ id, ...patch }),
  });
}

/** —— 删除 —— 优先 DELETE /entries/{id}，兼容旧 /entries/delete */
export async function deleteEntry(id: number) {
  try {
    const r = await fetch(`${API_BASE}/entries/${id}`, { method: "DELETE" });
    if (r.ok) return r;
    if (r.status !== 404 && r.status !== 405)
      throw new Error(`${r.status} ${r.statusText}`);
  } catch { /* 走旧式 */ }

  return fetch(`${API_BASE}/entries/delete`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ id }),
  });
}

/** —— 批量替换 —— 兼容多种后端路径 */
export async function bulkReplace(args: {
  keyword: string;
  replacement: string;
  scope?: "src" | "tgt" | "both";
  source_name?: string;
  date_from?: string;
  date_to?: string;
  regex_mode?: boolean;
  case_sensitive?: boolean;
  strict_word?: boolean;
  first_only?: boolean;
}) {
  const payload = { ...args };
  // 新：/entries/bulk-replace
  try {
    const r = await fetch(`${API_BASE}/entries/bulk-replace`, {
      method: "POST",
      headers: { "content-type": "application/json", accept: "application/json" },
      body: JSON.stringify(payload),
    });
    if (r.ok) return r.json();
    if (r.status !== 404 && r.status !== 405)
      throw new Error(`${r.status} ${r.statusText}`);
  } catch { /* 走旧式 */ }

  // 旧：/entries/replace
  const r2 = await fetch(`${API_BASE}/entries/replace`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r2.ok) throw new Error(`${r2.status} ${r2.statusText}`);
  return r2.json();
}
