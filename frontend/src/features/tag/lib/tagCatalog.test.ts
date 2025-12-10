import { describe, expect, it } from 'vitest';
import type { LibraryTagSummaryDto } from '@/entities/library';
import {
  buildTagDescriptionsMap,
  mergeTagDescriptionMaps,
  resolveTagDescription,
  findMissingTagLabels,
} from './tagCatalog';

let counter = 0;
const buildTag = (overrides: Partial<LibraryTagSummaryDto>): LibraryTagSummaryDto => ({
  id: overrides.id ?? `tag-${counter += 1}`,
  name: overrides.name ?? 'tag',
  description: overrides.description ?? 'desc',
  color: overrides.color ?? null,
  icon: overrides.icon ?? null,
  created_at: overrides.created_at ?? '2024-01-01T00:00:00Z',
  updated_at: overrides.updated_at ?? '2024-01-02T00:00:00Z',
});

describe('tagCatalog helpers', () => {
  it('builds scoped + unscoped keys when libraryId provided', () => {
    const map = buildTagDescriptionsMap([
      buildTag({ name: 'AI', description: 'Artificial Intelligence' }),
      buildTag({ name: ' Ops ', description: 'Operations' }),
    ], { libraryId: 'lib-1' });

    expect(map).toMatchObject({
      ai: 'Artificial Intelligence',
      'lib-1:ai': 'Artificial Intelligence',
      ops: 'Operations',
      'lib-1:ops': 'Operations',
    });
  });

  it('omits unscoped keys when includeUnscoped=false', () => {
    const map = buildTagDescriptionsMap([
      buildTag({ name: 'AI', description: 'Artificial Intelligence' }),
    ], { libraryId: 'lib-2', includeUnscoped: false });

    expect(map).toEqual({ 'lib-2:ai': 'Artificial Intelligence' });
  });

  it('resolves scoped value before fallback', () => {
    const merged = mergeTagDescriptionMaps(
      { ai: 'Generic AI' },
      { 'lib-3:ai': 'Library Specific AI' },
    );

    const resolved = resolveTagDescription('AI', merged, { libraryId: 'lib-3' });
    expect(resolved).toBe('Library Specific AI');
  });

  it('finds missing labels using scoped map awareness', () => {
    const map = { 'lib-4:ops': 'Operations' };
    const missing = findMissingTagLabels(['Ops', 'AI'], map, { libraryId: 'lib-4' });
    expect(missing).toEqual(['ai']);
  });
});
