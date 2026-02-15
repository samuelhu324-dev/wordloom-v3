"use client";

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as libraryApi from './api';
import type { LibrarySortOption } from './api';
import { UpdateLibraryRequest, LibraryDto, LibraryTagSummaryDto } from '@/entities/library';
import { searchTags } from '@/features/tag/model/api';
import {
  buildTagDescriptionsMap,
  mergeTagDescriptionMaps,
  findMissingTagLabels,
  normalizeTagLabel,
  type TagDescriptionsMap,
} from '@/features/tag/lib/tagCatalog';

const QUERY_KEY = ['libraries'];
const QUERY_KEY_DETAIL = (id: string) => [...QUERY_KEY, id];

interface UseLibrariesParams {
  query?: string;
  sort?: LibrarySortOption;
  includeArchived?: boolean;
}

/** Fetch libraries with optional search (debounced) */
export function useLibraries(params: UseLibrariesParams, initialData?: LibraryDto[]) {
  const debouncedQuery = useDebounce(params.query, 300);
  const sort = params.sort;
  const includeArchived = params.includeArchived;
  return useQuery<LibraryDto[]>({
    queryKey: [...QUERY_KEY, debouncedQuery, sort, includeArchived],
    queryFn: async () => {
      const started = performance.now();
      const data = await libraryApi.listLibraries({
        query: debouncedQuery || undefined,
        sort,
        includeArchived,
      });
      try {
        localStorage.setItem('wl_libraries_last_duration_ms', String(Math.round(performance.now() - started)));
      } catch (_) {}
      return data;
    },
    staleTime: 5 * 60 * 1000,
    placeholderData: (previous) => previous,
    initialData,
  });
}

function useDebounce<T>(value: T, ms: number): T {
  const [v, setV] = React.useState(value);
  React.useEffect(() => {
    const h = setTimeout(() => setV(value), ms);
    return () => clearTimeout(h);
  }, [value, ms]);
  return v;
}

/** Fetch single library */
export function useLibrary(id: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEY_DETAIL(id || ''),
    queryFn: async () => {
      const started = performance.now();
      const data = await libraryApi.getLibrary(id!);
      // mirror cache write (duration for diagnostics)
      try {
        localStorage.setItem(`wl_library_cache_${id}`, JSON.stringify({ ts: Date.now(), data }));
        localStorage.setItem(`wl_library_last_duration_ms_${id}`, String(Math.round(performance.now() - started)));
      } catch (_) {}
      return data;
    },
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });
}

/** Create library */
export function useCreateLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: libraryApi.createLibrary,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

/** Update library */
export function useUpdateLibrary(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: UpdateLibraryRequest) =>
      libraryApi.updateLibrary(id, request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY_DETAIL(id) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

/** Delete library */
export function useDeleteLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: libraryApi.deleteLibrary,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });
}

/** Record a library view and sync caches */
export function useRecordLibraryView() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (libraryId: string) => libraryApi.recordLibraryView(libraryId),
    onSuccess: (updatedLibrary) => {
      // Update list cache entries
      queryClient.setQueriesData({ queryKey: QUERY_KEY }, (oldData: unknown) => {
        if (!Array.isArray(oldData)) return oldData;
        return oldData.map((item: any) => (item.id === updatedLibrary.id ? updatedLibrary : item));
      });
      // Update detail cache
      queryClient.setQueryData(QUERY_KEY_DETAIL(updatedLibrary.id), updatedLibrary);
    },
  });
}

interface QuickUpdateInput {
  libraryId: string;
  data: Partial<UpdateLibraryRequest>;
}

/** Lightweight update for pinned/order/archive toggles */
export function useQuickUpdateLibrary() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ libraryId, data }: QuickUpdateInput) =>
      libraryApi.updateLibrary(libraryId, data),
    onSuccess: (updatedLibrary) => {
      // 仅更新基础字段，保留列表/详情中的 tags 以避免被旧值覆盖
      queryClient.setQueriesData({ queryKey: QUERY_KEY }, (oldData: unknown) => {
        if (!Array.isArray(oldData)) return oldData;
        return oldData.map((item: any) => {
          if (!item || item.id !== updatedLibrary.id) return item;
          const nextTags = item.tags ?? updatedLibrary.tags;
          const nextTagTotal = item.tag_total_count ?? updatedLibrary.tag_total_count;
          return { ...item, ...updatedLibrary, tags: nextTags, tag_total_count: nextTagTotal };
        });
      });

      queryClient.setQueryData(QUERY_KEY_DETAIL(updatedLibrary.id), (prev: any) => {
        if (!prev) return updatedLibrary;
        const nextTags = prev.tags ?? updatedLibrary.tags;
        const nextTagTotal = prev.tag_total_count ?? updatedLibrary.tag_total_count;
        return { ...prev, ...updatedLibrary, tags: nextTags, tag_total_count: nextTagTotal };
      });
      // 不在这里 invalidate，以免新的列表请求把更新后的 tags 覆盖回旧值
    },
  });
}

type LibraryThemeColorSource = 'cover' | 'theme' | 'hash';

export interface LibraryThemeColorState {
  hex: string;
  h: number;
  s: number;
  l: number;
  source: LibraryThemeColorSource;
}

interface UseLibraryThemeColorParams {
  libraryId?: string | null;
  libraryName?: string | null;
  coverUrl?: string | null;
  themeColor?: string | null;
  prefer?: 'cover-first' | 'theme-first';
  cache?: boolean;
  timeoutMs?: number;
}

interface CachedThemeColor extends LibraryThemeColorState {
  updatedAt: number;
  coverSignature?: string | null;
  themeSignature?: string | null;
}

const THEME_COLOR_CACHE = new Map<string, CachedThemeColor>();
const DEFAULT_THEME_TIMEOUT_MS = 4500;
const THEME_PRESET_COLORS: Record<string, string> = {
  'silk-blue': '#2e5e92',
  'silk_blue': '#2e5e92',
  'silkblue': '#2e5e92',
  silk: '#2e5e92',
  'business-blue': '#0066cc',
  'business_blue': '#0066cc',
  'businessblue': '#0066cc',
  business: '#0066cc',
  loom: '#5a7d99',
  'loom-dark': '#7a9db3',
  'loom_dark': '#7a9db3',
  loomdark: '#7a9db3',
  dark: '#4d9bff',
  default: '#2e5e92',
};

export function useLibraryThemeColor(params: UseLibraryThemeColorParams): LibraryThemeColorState {
  const {
    libraryId,
    libraryName,
    coverUrl,
    themeColor,
    prefer = 'cover-first',
    cache = true,
    timeoutMs = DEFAULT_THEME_TIMEOUT_MS,
  } = params;

  const normalizedTheme = React.useMemo(() => normalizeThemeColor(themeColor), [themeColor]);
  const hashedFallback = React.useMemo(() => {
    const seed = [libraryName, libraryId].filter(Boolean).join('__') || libraryId || 'library';
    return deterministicThemeColor(seed);
  }, [libraryId, libraryName]);

  const fallback = React.useMemo(
    () => normalizedTheme ?? hashedFallback,
    [normalizedTheme, hashedFallback]
  );

  const [color, setColor] = React.useState<LibraryThemeColorState>(fallback);

  React.useEffect(() => {
    setColor((prev) => (isSameColor(prev, fallback) ? prev : fallback));
  }, [fallback]);

  React.useEffect(() => {
    if (!libraryId) return;
    if (typeof window === 'undefined') return;

    const cacheKey = buildThemeCacheKey(libraryId);
    const coverSignature = coverUrl || null;
    const themeSignature = normalizedTheme?.hex ?? null;

    const cached = cache ? readThemeColorCache(cacheKey) : null;
    if (cached) {
      const coverMatches = coverSignature
        ? cached.coverSignature === coverSignature
        : !cached.coverSignature;
      const themeMatches = themeSignature
        ? !cached.themeSignature || cached.themeSignature === themeSignature
        : !cached.themeSignature;

      if (coverMatches && themeMatches) {
        if (normalizedTheme && cached.source === 'hash') {
          const nextState = normalizedTheme;
          setColor((prev) => (isSameColor(prev, nextState) ? prev : nextState));
          if (cache) {
            writeThemeColorCache(cacheKey, attachMetadata(nextState, coverSignature, themeSignature));
          }
          if (!coverUrl || prefer === 'theme-first') {
            return;
          }
        } else {
          const cachedState = stripCacheMetadata(cached);
          setColor((prev) => (isSameColor(prev, cachedState) ? prev : cachedState));
          if (cached.source === 'cover' || !coverUrl || prefer === 'theme-first') {
            return;
          }
        }
      }
    }

    if (!coverUrl || prefer === 'theme-first') {
      if (cache) {
        writeThemeColorCache(cacheKey, attachMetadata(fallback, null, themeSignature));
      }
      return;
    }

    let cancelled = false;
    const img = new Image();
    img.crossOrigin = 'anonymous';
    const timer = window.setTimeout(() => {
      if (cancelled) return;
      if (cache) {
        writeThemeColorCache(cacheKey, attachMetadata(fallback, null, themeSignature));
      }
    }, timeoutMs);

    const applyColor = (next: LibraryThemeColorState, signature: string | null) => {
      if (cancelled) return;
      setColor((prev) => (isSameColor(prev, next) ? prev : next));
      if (cache) {
        writeThemeColorCache(cacheKey, attachMetadata(next, signature, themeSignature));
      }
    };

    img.onload = () => {
      window.clearTimeout(timer);
      if (cancelled) return;
      try {
        const rgb = sampleImageDominantColor(img);
        const fromCover = createStateFromRgb(rgb, 'cover');
        const harmonized = normalizedTheme ? harmonizeWithTheme(fromCover, normalizedTheme) : fromCover;
        applyColor(harmonized, coverSignature);
      } catch (error) {
        if (process.env.NODE_ENV !== 'production') {
          console.warn(
            `[useLibraryThemeColor] failed to extract cover color for library ${libraryId}`,
            error
          );
        }
        applyColor(fallback, null);
      }
    };

    img.onerror = () => {
      window.clearTimeout(timer);
      if (cancelled) return;
      applyColor(fallback, null);
    };

    img.src = coverUrl;
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [libraryId, coverUrl, normalizedTheme, fallback, cache, prefer, timeoutMs]);

  return color;
}

function isSameColor(a: LibraryThemeColorState, b: LibraryThemeColorState): boolean {
  return a.hex === b.hex && a.source === b.source && a.h === b.h && a.s === b.s && a.l === b.l;
}

function buildThemeCacheKey(libraryId: string): string {
  return `wl_library_theme_${libraryId}`;
}

function stripCacheMetadata(value: CachedThemeColor): LibraryThemeColorState {
  return {
    hex: value.hex,
    h: value.h,
    s: value.s,
    l: value.l,
    source: value.source,
  };
}

function attachMetadata(
  state: LibraryThemeColorState,
  coverSignature: string | null,
  themeSignature: string | null,
): CachedThemeColor {
  return {
    ...state,
    updatedAt: Date.now(),
    coverSignature: coverSignature || null,
    themeSignature: themeSignature || null,
  };
}

function readThemeColorCache(key: string): CachedThemeColor | null {
  const memory = THEME_COLOR_CACHE.get(key);
  if (memory) return memory;
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    const normalized = normalizeCachedThemeColor(parsed);
    if (!normalized) return null;
    THEME_COLOR_CACHE.set(key, normalized);
    return normalized;
  } catch {
    return null;
  }
}

function writeThemeColorCache(key: string, value: CachedThemeColor) {
  THEME_COLOR_CACHE.set(key, value);
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore quota errors
  }
}

function normalizeCachedThemeColor(payload: any): CachedThemeColor | null {
  if (!payload || typeof payload.hex !== 'string') return null;
  const normalizedHex = normalizeHex(payload.hex);
  if (!normalizedHex) return null;
  const source: LibraryThemeColorSource =
    payload.source === 'cover' || payload.source === 'theme' || payload.source === 'hash'
      ? payload.source
      : 'hash';

  const hValue = typeof payload.h === 'number' ? payload.h : undefined;
  const sValue = typeof payload.s === 'number' ? payload.s : undefined;
  const lValue = typeof payload.l === 'number' ? payload.l : undefined;

  if (hValue == null || sValue == null || lValue == null) {
    const rgb = hexToRgb(normalizedHex);
    if (!rgb) return null;
    const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b);
    return {
      hex: normalizedHex,
      h: Math.round(hsl.h),
      s: Math.round(hsl.s),
      l: Math.round(hsl.l),
      source,
      updatedAt: typeof payload.updatedAt === 'number' ? payload.updatedAt : Date.now(),
      coverSignature: typeof payload.coverSignature === 'string' ? payload.coverSignature : null,
      themeSignature: typeof payload.themeSignature === 'string' ? payload.themeSignature : null,
    };
  }

  return {
    hex: normalizedHex,
    h: hValue,
    s: sValue,
    l: lValue,
    source,
    updatedAt: typeof payload.updatedAt === 'number' ? payload.updatedAt : Date.now(),
    coverSignature: typeof payload.coverSignature === 'string' ? payload.coverSignature : null,
    themeSignature: typeof payload.themeSignature === 'string' ? payload.themeSignature : null,
  };
}

function normalizeThemeColor(color?: string | null): LibraryThemeColorState | null {
  if (!color) return null;
  const presetHex = resolvePresetColor(color);
  if (presetHex) {
    const fromPreset = createStateFromHex(presetHex, 'theme');
    if (fromPreset) return fromPreset;
  }
  const byHex = createStateFromHex(color, 'theme');
  if (byHex) return byHex;
  const rgb = parseRgbColor(color);
  if (rgb) return createStateFromRgb(rgb, 'theme');
  const hsl = parseHslColor(color);
  if (hsl) return createStateFromHsl(hsl.h, hsl.s, hsl.l, 'theme');
  return null;
}

function deterministicThemeColor(seed: string): LibraryThemeColorState {
  const normalizedSeed = seed || 'library';
  let hash = 0;
  for (let i = 0; i < normalizedSeed.length; i += 1) {
    hash = (hash * 31 + normalizedSeed.charCodeAt(i)) >>> 0;
  }
  const hue = hash % 360;
  const saturation = 55 + (hash % 18); // 55-72
  const lightness = 46 + ((hash >> 3) % 14); // 46-59
  return createStateFromHsl(hue, saturation, lightness, 'hash');
}

function createStateFromHex(hex: string, source: LibraryThemeColorSource): LibraryThemeColorState | null {
  const rgb = hexToRgb(hex);
  if (!rgb) return null;
  return createStateFromRgb(rgb, source);
}

function createStateFromRgb(
  rgb: { r: number; g: number; b: number },
  source: LibraryThemeColorSource,
): LibraryThemeColorState {
  const { r, g, b } = rgb;
  const hsl = rgbToHsl(r, g, b);
  return {
    hex: rgbToHex(r, g, b),
    h: Math.round(hsl.h),
    s: Math.round(hsl.s),
    l: Math.round(hsl.l),
    source,
  };
}

function createStateFromHsl(
  h: number,
  s: number,
  l: number,
  source: LibraryThemeColorSource,
): LibraryThemeColorState {
  const normalizedH = ((h % 360) + 360) % 360;
  const normalizedS = clamp(s, 0, 100);
  const normalizedL = clamp(l, 0, 100);
  const rgb = hslToRgb(normalizedH, normalizedS, normalizedL);
  return {
    hex: rgbToHex(rgb.r, rgb.g, rgb.b),
    h: Math.round(normalizedH),
    s: Math.round(normalizedS),
    l: Math.round(normalizedL),
    source,
  };
}

function resolvePresetColor(raw?: string | null): string | null {
  if (!raw) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const lower = trimmed.toLowerCase();

  const direct = THEME_PRESET_COLORS[lower];
  if (direct) return direct;

  const hyphenated = lower.replace(/[\s_]+/g, '-').replace(/-+/g, '-');
  if (hyphenated) {
    const viaHyphen = THEME_PRESET_COLORS[hyphenated];
    if (viaHyphen) return viaHyphen;
  }

  const compact = hyphenated.replace(/-/g, '');
  if (compact) {
    const viaCompact = THEME_PRESET_COLORS[compact];
    if (viaCompact) return viaCompact;
  }

  return null;
}

function parseRgbColor(raw: string): { r: number; g: number; b: number } | null {
  const match = raw.trim().match(/^rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)/i);
  if (!match) return null;
  const r = Number(match[1]);
  const g = Number(match[2]);
  const b = Number(match[3]);
  if ([r, g, b].some((v) => Number.isNaN(v))) return null;
  return {
    r: clamp(Math.round(r), 0, 255),
    g: clamp(Math.round(g), 0, 255),
    b: clamp(Math.round(b), 0, 255),
  };
}

function parseHslColor(raw: string): { h: number; s: number; l: number } | null {
  const match = raw.trim().match(/^hsla?\(\s*([0-9.]+)\s*,\s*([0-9.]+)%\s*,\s*([0-9.]+)%/i);
  if (!match) return null;
  const h = Number(match[1]);
  const s = Number(match[2]);
  const l = Number(match[3]);
  if ([h, s, l].some((v) => Number.isNaN(v))) return null;
  return {
    h,
    s: clamp(s, 0, 100),
    l: clamp(l, 0, 100),
  };
}

function normalizeHex(raw: string): string | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const withoutHash = trimmed.startsWith('#') ? trimmed.slice(1) : trimmed;
  if (/^[0-9a-fA-F]{3}$/.test(withoutHash)) {
    const expanded = withoutHash
      .split('')
      .map((char) => char + char)
      .join('');
    return `#${expanded.toUpperCase()}`;
  }
  if (/^[0-9a-fA-F]{6}$/.test(withoutHash)) {
    return `#${withoutHash.toUpperCase()}`;
  }
  return null;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const normalized = normalizeHex(hex);
  if (!normalized) return null;
  const value = normalized.slice(1);
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16),
  };
}

function rgbToHex(r: number, g: number, b: number): string {
  const toHex = (value: number) => clamp(Math.round(value), 0, 255).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

function rgbToHsl(r: number, g: number, b: number): { h: number; s: number; l: number } {
  const rf = clamp(r, 0, 255) / 255;
  const gf = clamp(g, 0, 255) / 255;
  const bf = clamp(b, 0, 255) / 255;

  const max = Math.max(rf, gf, bf);
  const min = Math.min(rf, gf, bf);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case rf:
        h = (gf - bf) / d + (gf < bf ? 6 : 0);
        break;
      case gf:
        h = (bf - rf) / d + 2;
        break;
      default:
        h = (rf - gf) / d + 4;
        break;
    }
    h /= 6;
  }

  return {
    h: (h * 360 + 360) % 360,
    s: s * 100,
    l: l * 100,
  };
}

function hslToRgb(h: number, s: number, l: number): { r: number; g: number; b: number } {
  const hNorm = ((h % 360) + 360) % 360 / 360;
  const sNorm = clamp(s, 0, 100) / 100;
  const lNorm = clamp(l, 0, 100) / 100;

  if (sNorm === 0) {
    const value = Math.round(lNorm * 255);
    return { r: value, g: value, b: value };
  }

  const q = lNorm < 0.5 ? lNorm * (1 + sNorm) : lNorm + sNorm - lNorm * sNorm;
  const p = 2 * lNorm - q;

  const hueToRgb = (t: number) => {
    let temp = t;
    if (temp < 0) temp += 1;
    if (temp > 1) temp -= 1;
    if (temp < 1 / 6) return p + (q - p) * 6 * temp;
    if (temp < 1 / 2) return q;
    if (temp < 2 / 3) return p + (q - p) * (2 / 3 - temp) * 6;
    return p;
  };

  const r = hueToRgb(hNorm + 1 / 3);
  const g = hueToRgb(hNorm);
  const b = hueToRgb(hNorm - 1 / 3);

  return {
    r: Math.round(r * 255),
    g: Math.round(g * 255),
    b: Math.round(b * 255),
  };
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function sampleImageDominantColor(image: HTMLImageElement): { r: number; g: number; b: number } {
  const SAMPLE_SIZE = 32;
  const canvas = document.createElement('canvas');
  canvas.width = SAMPLE_SIZE;
  canvas.height = SAMPLE_SIZE;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  if (!context) {
    throw new Error('Canvas 2D context unavailable');
  }
  context.drawImage(image, 0, 0, SAMPLE_SIZE, SAMPLE_SIZE);
  const data = context.getImageData(0, 0, SAMPLE_SIZE, SAMPLE_SIZE).data;
  let r = 0;
  let g = 0;
  let b = 0;
  let count = 0;
  for (let i = 0; i < data.length; i += 4) {
    const alpha = data[i + 3];
    if (alpha < 32) continue;
    r += data[i];
    g += data[i + 1];
    b += data[i + 2];
    count += 1;
  }
  if (count === 0) {
    throw new Error('Unable to sample dominant color (no opaque pixels)');
  }
  return {
    r: Math.round(r / count),
    g: Math.round(g / count),
    b: Math.round(b / count),
  };
}

function harmonizeWithTheme(
  candidate: LibraryThemeColorState,
  theme: LibraryThemeColorState,
): LibraryThemeColorState {
  const distance = hueDistance(candidate.h, theme.h);
  if (distance <= 32) {
    return candidate;
  }

  const blendWeight = 0.65;
  const blendedS = clamp(theme.s * blendWeight + candidate.s * (1 - blendWeight), 20, 90);
  const blendedL = clamp(theme.l * blendWeight + candidate.l * (1 - blendWeight), 28, 74);

  return createStateFromHsl(theme.h, blendedS, blendedL, candidate.source);
}

function hueDistance(a: number, b: number): number {
  const diff = Math.abs(a - b) % 360;
  return diff > 180 ? 360 - diff : diff;
}

type LibraryTagCatalogFetchPolicy = 'missing-only' | 'always';

interface UseLibraryTagCatalogParams {
  libraryId?: string | null;
  inlineTags?: LibraryTagSummaryDto[] | null;
  requiredTagLabels?: Array<string | null | undefined>;
  limit?: number;
  enabled?: boolean;
  fetchPolicy?: LibraryTagCatalogFetchPolicy;
  includeUnscopedFromInline?: boolean;
  includeGlobalCatalog?: boolean;
  staleTimeMs?: number;
}

export function useLibraryTagCatalog(params: UseLibraryTagCatalogParams = {}) {
  const {
    libraryId: rawLibraryId,
    inlineTags,
    requiredTagLabels = [],
    limit = 200,
    enabled = true,
    fetchPolicy = 'missing-only',
    includeUnscopedFromInline = true,
    includeGlobalCatalog = true,
    staleTimeMs = 5 * 60 * 1000,
  } = params;

  const libraryId = rawLibraryId || null;

  const inlineTagDescriptions = React.useMemo<TagDescriptionsMap | undefined>(
    () => buildTagDescriptionsMap(inlineTags, {
      libraryId,
      includeUnscoped: includeUnscopedFromInline,
    }),
    [inlineTags, libraryId, includeUnscopedFromInline],
  );

  const missingLabelsFromInline = React.useMemo(
    () => findMissingTagLabels(requiredTagLabels, inlineTagDescriptions, { libraryId }),
    [requiredTagLabels, inlineTagDescriptions, libraryId],
  );

  const shouldFetchLibraryCatalog = Boolean(libraryId)
    && enabled
    && (fetchPolicy === 'always' ? true : missingLabelsFromInline.length > 0);

  const queryResult = useQuery<libraryApi.LibraryTagsResponseDto>({
    queryKey: ['library-tag-catalog', libraryId, limit],
    queryFn: () => libraryApi.getLibraryTags(libraryId!, limit),
    enabled: shouldFetchLibraryCatalog,
    staleTime: staleTimeMs,
  });

  const fetchedTagDescriptions = React.useMemo<TagDescriptionsMap | undefined>(
    () => buildTagDescriptionsMap(queryResult.data?.tags, { libraryId, includeUnscoped: true }),
    [queryResult.data?.tags, libraryId],
  );

  const libraryTagDescriptions = React.useMemo(
    () => mergeTagDescriptionMaps(inlineTagDescriptions, fetchedTagDescriptions),
    [inlineTagDescriptions, fetchedTagDescriptions],
  );

  const missingLabelsAfterLibrary = React.useMemo(
    () => findMissingTagLabels(requiredTagLabels, libraryTagDescriptions, { libraryId }),
    [requiredTagLabels, libraryTagDescriptions, libraryId],
  );

  const normalizedGlobalTargets = React.useMemo(() => {
    if (!includeGlobalCatalog || missingLabelsAfterLibrary.length === 0) {
      return [] as Array<{ label: string; normalized: string }>;
    }
    const seen = new Set<string>();
    const targets: Array<{ label: string; normalized: string }> = [];
    missingLabelsAfterLibrary.forEach((label) => {
      const normalized = normalizeTagLabel(label);
      if (!normalized || seen.has(normalized)) {
        return;
      }
      seen.add(normalized);
      targets.push({ label: label || normalized, normalized });
    });
    return targets;
  }, [missingLabelsAfterLibrary, includeGlobalCatalog]);

  const shouldFetchGlobalCatalog = normalizedGlobalTargets.length > 0 && enabled;

  const globalTagQuery = useQuery<TagDescriptionsMap | null>({
    queryKey: [
      'global-tag-catalog',
      normalizedGlobalTargets.map((target) => target.normalized).sort().join('|'),
    ],
    queryFn: async () => {
      const data = await fetchGlobalTagDescriptions(normalizedGlobalTargets);
      return data ?? null;
    },
    enabled: shouldFetchGlobalCatalog,
    staleTime: staleTimeMs,
    initialData: null,
  });

  const tagDescriptionsMap = React.useMemo(
    () => mergeTagDescriptionMaps(libraryTagDescriptions, globalTagQuery.data),
    [libraryTagDescriptions, globalTagQuery.data],
  );

  const combinedTags = React.useMemo(() => {
    const sources: LibraryTagSummaryDto[][] = [];
    if (Array.isArray(inlineTags) && inlineTags.length > 0) {
      sources.push(inlineTags);
    }
    if (Array.isArray(queryResult.data?.tags) && queryResult.data.tags.length > 0) {
      sources.push(queryResult.data.tags);
    }
    if (!sources.length) {
      return undefined;
    }
    const seen = new Set<string>();
    const ordered: LibraryTagSummaryDto[] = [];
    const pushUnique = (tag?: LibraryTagSummaryDto) => {
      if (!tag) return;
      const key = tag.id || normalizeTagLabel(tag.name);
      if (!key || seen.has(key)) {
        return;
      }
      seen.add(key);
      ordered.push(tag);
    };
    sources.forEach((collection) => collection.forEach(pushUnique));
    return ordered;
  }, [inlineTags, queryResult.data?.tags]);

  const missingLabels = React.useMemo(
    () => findMissingTagLabels(requiredTagLabels, tagDescriptionsMap, { libraryId }),
    [requiredTagLabels, tagDescriptionsMap, libraryId],
  );

  return {
    ...queryResult,
    tagDescriptionsMap,
    inlineTagDescriptions,
    fetchedTagDescriptions,
    globalTagDescriptions: globalTagQuery.data,
    tags: combinedTags,
    missingLabels,
    shouldFetch: shouldFetchLibraryCatalog,
  };
}

async function fetchGlobalTagDescriptions(
  targets: Array<{ label: string; normalized: string }>,
): Promise<TagDescriptionsMap | null> {
  if (!targets.length) {
    return null;
  }

  const results = await Promise.all(targets.map(async ({ label, normalized }) => {
    try {
      const matches = await searchTags({ keyword: label, limit: 12 });
      const exact = matches.find((tag) => normalizeTagLabel(tag.name) === normalized);
      const description = exact?.description?.trim();
      if (!description) {
        return null;
      }
      return { key: normalized, description };
    } catch (error) {
      console.warn('[useLibraryTagCatalog] failed to load tag description', label, error);
      return null;
    }
  }));

  const map: TagDescriptionsMap = {};
  let hasEntries = false;

  results.forEach((entry) => {
    if (!entry) {
      return;
    }
    map[entry.key] = entry.description;
    hasEntries = true;
  });

  return hasEntries ? map : null;
}
