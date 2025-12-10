import { exportAppearance, importAppearance, AppearanceExport } from "./prefs";

/** 将外观导出为 URL 参数（base64） */
export function appearanceToParam(data: AppearanceExport = exportAppearance()): string {
  const json = JSON.stringify(data);
  if (typeof btoa !== "undefined") return btoa(unescape(encodeURIComponent(json)));
  // Node 兜底：
  // @ts-ignore
  return Buffer.from(json, "utf8").toString("base64");
}

/** 从 URL 参数读取并应用外观（无就跳过） */
export function applyAppearanceFromUrl(paramKey = "appearance"): boolean {
  if (typeof window === "undefined") return false;
  const url = new URL(window.location.href);
  const token = url.searchParams.get(paramKey);
  if (!token) return false;
  try {
    const json = decodeURIComponent(escape(atob(token)));
    const data = JSON.parse(json);
    importAppearance(data);
    return true;
  } catch (e) {
    console.error("Failed to parse appearance param:", e);
    return false;
  }
}

export type AppearanceFlags = { readonly?: boolean; allowImport?: boolean };

/** 解析 URL 外观预览的控制开关 */
export function parseAppearanceFlags(paramKey = "appearance_mode"): AppearanceFlags {
  if (typeof window === "undefined") return {};
  const url = new URL(window.location.href);
  const mode = (url.searchParams.get(paramKey) || "").toLowerCase();
  const allowImport = url.searchParams.get("allowImport") === "1";
  return {
    readonly: mode === "readonly",
    allowImport,
  };
}

/** 生成带预览参数的 URL；可设置只读与是否允许导入 */
export function buildPreviewUrl(
  data: AppearanceExport = exportAppearance(),
  opts: AppearanceFlags = {},
  paramKey = "appearance",
): string {
  if (typeof window === "undefined") return "";
  const url = new URL(window.location.href);
  url.searchParams.set(paramKey, appearanceToParam(data));
  if (opts.readonly) url.searchParams.set("appearance_mode", "readonly"); else url.searchParams.delete("appearance_mode");
  if (opts.allowImport) url.searchParams.set("allowImport", "1"); else url.searchParams.delete("allowImport");
  return url.toString();
}

// next/src/lib/appearanceUrl.ts

// 静态资源前缀（Nginx/Next 静态映射），默认 /orbit-assets
const ASSET_PREFIX = process.env.NEXT_PUBLIC_ORBIT_ASSET_PREFIX ?? '/orbit-assets';

/**
 * assetUrl
 * - 绝对 URL：原样返回
 * - 相对路径：拼上 ASSET_PREFIX
 */
export function assetUrl(relOrAbs?: string | null): string {
  if (!relOrAbs) return '';
  try {
    const u = new URL(relOrAbs);
    return u.toString();
  } catch {
    // 非绝对：按相对处理
  }
  const leading = relOrAbs.startsWith('/') ? '' : '/';
  return `${ASSET_PREFIX}${leading}${relOrAbs}`;
}

export { ASSET_PREFIX };
