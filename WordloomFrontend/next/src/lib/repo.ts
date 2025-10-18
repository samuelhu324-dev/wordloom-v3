// 仅微调：新增一个安全的分页获取函数，兼容两种返回格式
export type Entry = {
  id: number;
  source_id?: number;
  en?: string;
  zh?: string;
  created_at?: string;
  // ...保持你现有字段不动
};

export type PageResult<T> = {
  items: T[];
  total: number;
};

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  // 保底：与你后端 run_backend.bat 默认一致（如 http://127.0.0.1:8000）
  "http://127.0.0.1:8000";

function parseTotalFromHeaders(h: Headers) {
  const raw = h.get("X-Total-Count") ?? h.get("x-total-count");
  return raw ? Number(raw) : NaN;
}

/**
 * 统一分页获取：
 * - 传入 1-based page 与 pageSize
 * - 兼容 {items,total} 或 [array] + X-Total-Count
 * - 越界页返回 {items:[], total:上一页的total或0}
 */
export async function fetchEntriesPage(
  page: number,
  pageSize: number
): Promise<PageResult<Entry>> {
  const safePage = Math.max(1, Math.floor(page || 1));
  const size = Math.max(1, Math.floor(pageSize || 20));

  const url = new URL(`${API_BASE}/entries`);
  url.searchParams.set("page", String(safePage));
  url.searchParams.set("page_size", String(size));

  const res = await fetch(url.toString(), {
    method: "GET",
    headers: { "Content-Type": "application/json" },
    // 允许跨域的情况下，后端 CORS 你已“已完成”
    // credentials: "include", // 如未来有鉴权可打开
  });

  if (!res.ok) {
    // 非 2xx 也不要炸；返回空数组，交给 UI 兜底
    return { items: [], total: 0 };
  }

  // 可能是 {items,total}
  try {
    const data = await res.json();
    // 结构1：显式 items/total
    if (data && Array.isArray(data.items) && typeof data.total === "number") {
      return { items: data.items as Entry[], total: data.total as number };
    }
    // 结构2：纯数组 + 头部 total
    if (Array.isArray(data)) {
      const hdrTotal = parseTotalFromHeaders(res.headers);
      return { items: data as Entry[], total: Number.isFinite(hdrTotal) ? hdrTotal : data.length };
    }
    // 其它非常规结构：尽量兜底
    return { items: [], total: 0 };
  } catch {
    // JSON 解析失败也兜底
    return { items: [], total: 0 };
  }
}
