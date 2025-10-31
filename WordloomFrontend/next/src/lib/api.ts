// 统一 API 客户端：支持多后端（优先相对路径 + Next 重写，必要时才用绝对地址）
const RAW_BASE = (process.env.NEXT_PUBLIC_API_BASE || "").trim();
const LOOM_BASE = (process.env.NEXT_PUBLIC_LOOM_API_BASE || "").trim();
const ORBIT_BASE_ENV = (process.env.NEXT_PUBLIC_ORBIT_API_BASE || "").trim();
const FORCE_ABSOLUTE = (process.env.NEXT_PUBLIC_FORCE_ABSOLUTE_API || "").trim() === "1";

// 默认后端
export const API_BASE = RAW_BASE.replace(/\/$/, "");
// Loom 专用后端（默认同 API_BASE）
export const LOOM_API_BASE = LOOM_BASE ? LOOM_BASE.replace(/\/$/, "") : API_BASE;
// Orbit 专用后端（默认同 API_BASE）
export const ORBIT_API_BASE_CONFIGURED = ORBIT_BASE_ENV ? ORBIT_BASE_ENV.replace(/\/$/, "") : API_BASE;

function isAbs(u: string) {
  return /^https?:\/\//i.test(u);
}

// 根据路径选择合适的后端基础地址（仅在 FORCE_ABSOLUTE 时启用）
function getApiBaseForPath(path: string): string {
  if (!FORCE_ABSOLUTE) return ""; // 默认走相对路径，由 Next 重写代理
  if (path.startsWith("/api/orbit")) return ORBIT_API_BASE_CONFIGURED;
  if (path.startsWith("/api/common")) return LOOM_API_BASE;
  return API_BASE;
}

export function resolveApiUrl(path: string) {
  if (!path) throw new Error("resolveApiUrl: empty path");
  if (isAbs(path)) return path;
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = getApiBaseForPath(p);
  return base ? `${base}${p}` : p; // 默认返回相对路径
}

export async function apiFetch<T = any>(path: string, init: RequestInit = {}): Promise<T> {
  const url = isAbs(path) ? path : resolveApiUrl(path);

  const headers = new Headers(init.headers);
  let body: any = (init as any).body;

  const isFormData = typeof FormData !== "undefined" && body instanceof FormData;
  const isBlob = typeof Blob !== "undefined" && body instanceof Blob;
  const isArrayBuffer = typeof ArrayBuffer !== "undefined" && body instanceof ArrayBuffer;
  const isTypedArray = typeof ArrayBuffer !== "undefined" && ArrayBuffer.isView && ArrayBuffer.isView(body as any);
  const isPlainObject =
    body && typeof body === "object" && !isFormData && !isBlob && !isArrayBuffer && !isTypedArray;

  // 自动 JSON 头与序列化
  if (isPlainObject && !headers.get("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (isPlainObject && headers.get("Content-Type")?.includes("application/json")) {
    body = JSON.stringify(body);
  }

  const res = await fetch(url, { ...init, headers, body });

  if (!res.ok) {
    const ct = res.headers.get("Content-Type") || "";
    const text = await res.text().catch(() => "");
    if (ct.includes("text/html")) {
      // HTML 多为前端 404/代理未命中，给出更明确提示
      throw new Error(`HTTP ${res.status} ${res.statusText}: HTML response from ${url}. Possible wrong server/port or dev rewrite not applied.`);
    }
    throw new Error(`HTTP ${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }

  if (res.status === 204) return undefined as unknown as T;

  const ct = res.headers.get("Content-Type") || "";
  if (ct.includes("application/json")) return (await res.json()) as T;

  // 兜底文本
  const txt = await res.text();
  return txt as unknown as T;
}