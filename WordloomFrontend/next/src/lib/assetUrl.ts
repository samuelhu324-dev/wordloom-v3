// src/lib/assetUrl.ts
import { ORBIT_ASSET_PREFIX } from '@/lib/apiBase';

export function assetUrl(relOrAbs?: string | null): string {
  if (!relOrAbs) return '';
  try { return new URL(relOrAbs).toString(); } catch { /* 非绝对路径，继续 */ }
  const leading = relOrAbs.startsWith('/') ? '' : '/';
  return `${ORBIT_ASSET_PREFIX}${leading}${relOrAbs}`;
}
