import { describe, it, expect } from 'vitest';
import { computeFractionalIndex, sortBlocksByFractionalIndex } from './fractionalOrder';
import type { BlockDto } from '@/entities/block';

describe('computeFractionalIndex', () => {
  it('falls back to provided value when neighbours are missing', () => {
    expect(computeFractionalIndex(undefined, undefined, 42)).toBe('42');
  });

  it('halves the after value when inserting before the first block', () => {
    expect(computeFractionalIndex(undefined, '10')).toBe('5');
  });

  it('increments the before value when appending to the end', () => {
    expect(computeFractionalIndex('7', undefined)).toBe('8');
  });

  it('returns the midpoint between surrounding blocks', () => {
    expect(computeFractionalIndex('3', '5')).toBe('4');
  });

  it('nudges forward if both neighbours share the same index', () => {
    expect(computeFractionalIndex('2', '2')).toBe('2.001');
  });
});

describe('sortBlocksByFractionalIndex', () => {
  const block = (id: string, fractionalIndex: string): BlockDto => ({
    id,
    book_id: 'book',
    type: 'text',
    content: { text: '' },
    fractional_index: fractionalIndex,
    kind: 'paragraph',
    heading_level: null,
    order: fractionalIndex,
    soft_deleted_at: null,
    created_at: new Date(0).toISOString(),
    updated_at: new Date(0).toISOString(),
  });

  it('orders blocks numerically even when strings are unsorted', () => {
    const unordered = [block('b', '10'), block('a', '2'), block('c', '7')];
    const sorted = sortBlocksByFractionalIndex(unordered);
    expect(sorted.map((item) => item.id)).toEqual(['a', 'c', 'b']);
  });

  it('pushes blocks with invalid fractional indexes to the top deterministically', () => {
    const custom = [block('alpha', 'foo'), block('beta', '1.5'), block('gamma', '0.5')];
    const sorted = sortBlocksByFractionalIndex(custom);
    expect(sorted.map((item) => item.id)).toEqual(['alpha', 'gamma', 'beta']);
  });
});
