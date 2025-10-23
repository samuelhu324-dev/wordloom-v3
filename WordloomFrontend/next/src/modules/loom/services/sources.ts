// src/modules/loom/services/sources.ts
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/common";

export type SourceLite = { id?: number | string; name: string };

// 兜底 fetch：按多个候选路径尝试，取第一个 200
async function fetchAny(paths: string[]): Promise<Response> {
  let lastErr: any;
  for (const p of paths) {
    try {
      const r = await fetch(`${API_BASE}${p}`, { headers: { accept: "application/json" } });
      if (r.ok) return r;
      lastErr = new Error(`${r.status} ${r.statusText}`);
    } catch (e) {
      lastErr = e;
    }
  }
  throw lastErr;
}

// 将各种返回形状规范化为 {id?, name}
function normalizeSources(data: any): SourceLite[] {
  const out: SourceLite[] = [];

  if (Array.isArray(data)) {
    for (const it of data) {
      if (!it) continue;
      // 1) 纯字符串
      if (typeof it === "string") {
        const name = it.trim();
        if (name) out.push({ name });
        continue;
      }
      // 2) 对象：常见字段
      if (typeof it === "object") {
        const name =
          (it.name ?? it["Name"] ?? it["source_name"] ?? it["title"] ?? "").toString().trim();
        if (name) {
          const id = it.id ?? it["ID"] ?? it["source_id"];
          out.push({ id, name });
        }
      }
    }
  }

  // 去空 & 去重（按 name）
  const seen = new Set<string>();
  const unique = out.filter((s) => {
    const n = s.name;
    if (!n) return false;
    if (seen.has(n)) return false;
    seen.add(n);
    return true;
  });

  // 按拼音/字母排序（简单 localeCompare）
  unique.sort((a, b) => a.name.localeCompare(b.name));
  return unique;
}

/** 列出所有来源（兼容 string[] / 对象数组；兼容多路由） */
export async function listSources(): Promise<SourceLite[]> {
  const r = await fetchAny([
    "/sources",       // 新
    "/sources/",      // 带尾斜杠
    "/sources/list",  // 旧
  ]);
  const json = await r.json();
  return normalizeSources(json);
}

/** 重命名来源（支持预览） */
export async function renameSource(
  from: string,
  to: string,
  preview = true
): Promise<{ changed?: number; updated?: number; count?: number }> {
  const r = await fetch(`${API_BASE}/sources/rename`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "application/json" },
    body: JSON.stringify({ from, to, preview }),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}
