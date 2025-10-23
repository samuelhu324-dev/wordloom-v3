// src/modules/loom/services/sources.ts
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api/common";

type SourceDTO = { id: number; name: string; url?: string | null };

async function getJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, { ...init, headers: { "accept": "application/json", "content-type": "application/json", ...(init?.headers||{}) }});
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

/** 列出所有来源（容错：/sources 或 /sources/list 都尝试） */
export async function listSources(): Promise<{id: number; name: string}[]> {
  try {
    const data = await getJSON<SourceDTO[]>(`${API_BASE}/sources`);
    return data.map(x => ({ id: x.id, name: x.name }));
  } catch {
    const data = await getJSON<SourceDTO[]>(`${API_BASE}/sources/list`);
    return data.map(x => ({ id: x.id, name: x.name }));
  }
}

/** 重命名来源（支持预览） */
export async function renameSource(from: string, to: string, preview = true): Promise<{changed?: number; updated?: number; count?: number}> {
  return getJSON(`${API_BASE}/sources/rename`, {
    method: "POST",
    body: JSON.stringify({ from, to, preview })
  });
}
