
/**
 * src/lib/repo.ts  — Minimal, non-destructive adapter for your backend.
 * - Uses GET for search (backend exposes GET /entries/search)
 * - Uses GET for sources at /sources/
 * - Cleans payloads (omits empty strings, 'all', '(Any)') to avoid accidental strict filtering
 * - Does not change any page/component logic; only centralizes API calls.
 */

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE as string) || "/api";
const SOURCES_ENDPOINT = (process.env.NEXT_PUBLIC_SOURCES_ENDPOINT as string) || "/sources/";
const SEARCH_ENDPOINT = (process.env.NEXT_PUBLIC_SEARCH_ENDPOINT as string) || "/entries/search";

function joinPath(path: string) {
  const base = API_BASE.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  return (base + p).replace(/\/+$/, "") + (p.endsWith("/") ? "/" : "");
}

export function buildUrl(path: string, query?: Record<string, any>) {
  const base = API_BASE.replace(/\/+$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  const u = new URL(base + p, "http://dummy.local");
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v === undefined || v === null) return;
      if (typeof v === "string" && v.trim() === "") return;
      u.searchParams.set(k, String(v));
    });
  }
  // return path + search (strip dummy origin)
  return u.pathname + (u.search ? u.search : "");
}

/** Normalize and remove empty-ish values before sending as query params */
function cleanParams(obj?: Record<string, any>) {
  const out: Record<string, any> = {};
  if (!obj) return out;
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null) continue;
    if (typeof v === "string") {
      const t = v.trim();
      if (t === "" || t.toLowerCase() === "all" || t === "(any)") continue;
      out[k] = t;
    } else if (typeof v === "number" && !Number.isNaN(v)) {
      out[k] = v;
    } else if (typeof v === "boolean") {
      out[k] = v;
    } else {
      out[k] = v;
    }
  }
  return out;
}

/** GET sources list (q optional) */
export async function listSources(params?: { q?: string; limit?: number }) {
  // Use the canonical backend route /sources/
  const url = buildUrl(SOURCES_ENDPOINT, {
    q: params?.q ?? undefined,
    limit: params?.limit ?? 200,
  });
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) {
    // fallback to /sources (no trailing slash)
    const fallback = buildUrl("/sources", {
      q: params?.q ?? undefined,
      limit: params?.limit ?? 200,
    });
    const r2 = await fetch(fallback, { cache: "no-store" });
    if (!r2.ok) throw new Error(`Sources fetch failed: ${r.status}`);
    return r2.json();
  }
  return r.json();
}

/** GET entries search with flexible params (backend expects GET) */
export async function searchEntries(raw: Record<string, any> = {}) {
  const params = cleanParams({
    q: raw.q ?? raw.keyword ?? raw.keyword?.toString?.() ?? undefined,
    source_name: raw.source_name ?? raw.source ?? raw.sourceName ?? undefined,
    limit: typeof raw.limit === "string" ? parseInt(raw.limit) : raw.limit ?? undefined,
    offset: typeof raw.offset === "string" ? parseInt(raw.offset) : raw.offset ?? undefined,
    sort: raw.sort ?? undefined,
  });

  const url = buildUrl(SEARCH_ENDPOINT, params);
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) {
    // Try legacy fallback path
    const fallback = buildUrl("/entries/search", params);
    const r2 = await fetch(fallback, { cache: "no-store" });
    if (!r2.ok) throw new Error(`Search failed: ${r.status}`);
    return r2.json();
  }
  return r.json();
}
