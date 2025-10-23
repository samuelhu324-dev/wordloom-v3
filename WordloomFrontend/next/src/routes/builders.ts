import { resolveAppPath } from "./map-app";
import { resolveApiPath } from "./map-api";
import type { AppToken, ApiToken } from "./tokens";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "";

export function buildAppPath(token: AppToken, params?: Record<string,string>, query?: Record<string,any>) {
  return resolveAppPath(token, params, query);
}

export function buildApiUrl(token: ApiToken, pathParams?: Record<string,string>, query?: Record<string, any>) {
  const path = resolveApiPath(token, pathParams);
  const url = new URL(API_BASE.replace(/\/+$/,"") + path, "http://x"); // base 假解析
  if (query) for (const [k,v] of Object.entries(query)) if (v!==undefined && v!=="") url.searchParams.set(k, String(v));
  return url.pathname + url.search;  // 交给 fetch 相对路径，由 dev 代理或 NGINX 解决
}
