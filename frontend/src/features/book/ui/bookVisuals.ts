import {
  Archive,
  BookOpenCheck,
  Sprout,
  TreePine,
  type LucideIcon,
} from 'lucide-react';
import { BookMaturity } from '@/entities/book';

export type MaturityVisualMeta = {
  label: string;
  short: string;
  pillBg: string;
  pillColor: string;
  iconColor: string;
  icon: LucideIcon;
};

export const STATUS_COLORS: Record<string, string> = {
  DRAFT: '#475569',
  PUBLISHED: '#16A34A',
  ARCHIVED: '#78350F',
  DELETED: '#DC2626',
};

export const MATURITY_META: Record<BookMaturity, MaturityVisualMeta> = {
  seed: {
    label: 'Seed · 草创',
    short: 'Seed',
    pillBg: 'rgba(34, 197, 94, 0.16)',
    pillColor: '#15803d',
    iconColor: '#16a34a',
    icon: Sprout,
  },
  growing: {
    label: 'Growing · 成长',
    short: 'Growing',
    pillBg: 'rgba(14, 165, 233, 0.18)',
    pillColor: '#0e7490',
    iconColor: '#0ea5e9',
    icon: TreePine,
  },
  stable: {
    label: 'Stable · 稳定',
    short: 'Stable',
    pillBg: 'rgba(29, 78, 216, 0.15)',
    pillColor: '#1d4ed8',
    iconColor: '#1d4ed8',
    icon: BookOpenCheck,
  },
  legacy: {
    label: 'Legacy · 归档',
    short: 'Legacy',
    pillBg: 'rgba(107, 114, 128, 0.2)',
    pillColor: '#6b7280',
    iconColor: '#6b7280',
    icon: Archive,
  },
};

const RELATIVE_TABLE: Array<{ unit: Intl.RelativeTimeFormatUnit; seconds: number }> = [
  { unit: 'year', seconds: 60 * 60 * 24 * 365 },
  { unit: 'month', seconds: 60 * 60 * 24 * 30 },
  { unit: 'week', seconds: 60 * 60 * 24 * 7 },
  { unit: 'day', seconds: 60 * 60 * 24 },
  { unit: 'hour', seconds: 60 * 60 },
  { unit: 'minute', seconds: 60 },
];

const relativeFormatterCache = new Map<string, Intl.RelativeTimeFormat>();

const getRelativeFormatter = (locale: string) => {
  if (typeof Intl === 'undefined') {
    return null;
  }
  const normalized = locale || 'zh-CN';
  if (!relativeFormatterCache.has(normalized)) {
    relativeFormatterCache.set(normalized, new Intl.RelativeTimeFormat(normalized, { numeric: 'auto' }));
  }
  return relativeFormatterCache.get(normalized)!;
};

const getRelativeFallback = (locale: string) => (locale?.toLowerCase().startsWith('en') ? 'just now' : '刚刚');

export const formatRelativeTime = (iso?: string | null, locale: string = 'zh-CN'): string => {
  const formatter = getRelativeFormatter(locale);
  if (!iso || !formatter) {
    return getRelativeFallback(locale);
  }

  const diffInSeconds = Math.round((new Date(iso).getTime() - Date.now()) / 1000);
  for (const entry of RELATIVE_TABLE) {
    if (Math.abs(diffInSeconds) >= entry.seconds) {
      return formatter.format(Math.round(diffInSeconds / entry.seconds), entry.unit);
    }
  }
  return formatter.format(0, 'minute');
};

export const formatBlockCount = (count?: number, locale: string = 'zh-CN') => {
  const value = count ?? 0;
  return locale?.toLowerCase().startsWith('en') ? `${value} blocks` : `${value} 个内容块`;
};
