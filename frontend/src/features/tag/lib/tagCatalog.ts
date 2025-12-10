import type { LibraryTagSummaryDto } from '@/entities/library';

export type TagDescriptionsMap = Record<string, string>;

export interface BuildTagDescriptionsOptions {
  libraryId?: string | null;
  includeUnscoped?: boolean;
}

const DEFAULT_INCLUDE_UNSCOPED = true;

export const normalizeTagLabel = (label?: string | null): string => {
  return label?.trim().toLowerCase() ?? '';
};

export const buildScopedTagKey = (label: string, libraryId?: string | null): string | null => {
  if (!label) {
    return null;
  }
  return libraryId ? `${libraryId}:${label}` : null;
};

export function buildTagDescriptionsMap(
  tags?: LibraryTagSummaryDto[] | null,
  options?: BuildTagDescriptionsOptions,
): TagDescriptionsMap | undefined {
  if (!tags || tags.length === 0) {
    return undefined;
  }

  const includeUnscoped = options?.includeUnscoped ?? DEFAULT_INCLUDE_UNSCOPED;
  const scopedLibraryId = options?.libraryId ?? null;
  const next: TagDescriptionsMap = {};
  let hasEntries = false;

  tags.forEach((tag) => {
    const label = normalizeTagLabel(tag?.name);
    const description = tag?.description?.trim();
    if (!label || !description) {
      return;
    }

    if (includeUnscoped && !next[label]) {
      next[label] = description;
      hasEntries = true;
    }

    if (scopedLibraryId) {
      const scopedKey = buildScopedTagKey(label, scopedLibraryId);
      if (scopedKey && !next[scopedKey]) {
        next[scopedKey] = description;
        hasEntries = true;
      }
    }
  });

  return hasEntries ? next : undefined;
}

export function mergeTagDescriptionMaps(
  ...maps: Array<TagDescriptionsMap | null | undefined>
): TagDescriptionsMap | undefined {
  const merged: TagDescriptionsMap = {};
  let hasEntries = false;

  maps.forEach((map) => {
    if (!map) {
      return;
    }
    Object.entries(map).forEach(([key, value]) => {
      merged[key] = value;
      hasEntries = true;
    });
  });

  return hasEntries ? merged : undefined;
}

export function resolveTagDescription(
  label?: string | null,
  map?: TagDescriptionsMap,
  options?: { libraryId?: string | null },
): string | undefined {
  if (!map) {
    return undefined;
  }
  const normalized = normalizeTagLabel(label);
  if (!normalized) {
    return undefined;
  }

  const libraryId = options?.libraryId ?? null;
  const scopedKey = buildScopedTagKey(normalized, libraryId);
  return (scopedKey && map[scopedKey]) || map[normalized];
}

export function findMissingTagLabels(
  labels: Array<string | null | undefined>,
  map?: TagDescriptionsMap,
  options?: { libraryId?: string | null },
): string[] {
  if (!labels?.length) {
    return [];
  }
  const libraryId = options?.libraryId ?? null;
  return labels
    .map((label) => normalizeTagLabel(label))
    .filter((label): label is string => Boolean(label))
    .filter((normalized) => {
      if (!map) {
        return true;
      }
      const scopedKey = buildScopedTagKey(normalized, libraryId);
      return !map[normalized] && !(scopedKey && map[scopedKey]);
    });
}
