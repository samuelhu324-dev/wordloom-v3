import { BlockDto } from '@/entities/block';

export const parseFractionalIndex = (value?: string | null): number | undefined => {
  if (!value) return undefined;
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : undefined;
};

export const computeFractionalIndex = (
  before?: string,
  after?: string,
  fallback: number = 1
): string => {
  const beforeVal = parseFractionalIndex(before);
  const afterVal = parseFractionalIndex(after);
  if (beforeVal === undefined && afterVal === undefined) return String(fallback);
  if (beforeVal === undefined && afterVal !== undefined) return String(afterVal / 2);
  if (beforeVal !== undefined && afterVal === undefined) return String(beforeVal + 1);
  if (beforeVal !== undefined && afterVal !== undefined) {
    if (beforeVal === afterVal) {
      return String(beforeVal + 0.001);
    }
    return String((beforeVal + afterVal) / 2);
  }
  return String(fallback);
};

export const sortBlocksByFractionalIndex = (blocks: BlockDto[]): BlockDto[] => {
  return [...blocks].sort((a, b) => {
    const aVal = parseFractionalIndex(a.fractional_index);
    const bVal = parseFractionalIndex(b.fractional_index);
    if (aVal === undefined && bVal === undefined) return 0;
    if (aVal === undefined) return -1;
    if (bVal === undefined) return 1;
    return aVal - bVal;
  });
};
