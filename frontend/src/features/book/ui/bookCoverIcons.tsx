import type { LucideIcon } from 'lucide-react';
import {
  BookCoverIconGroup,
  BookCoverIconId,
  BookCoverIconMeta,
  BOOK_COVER_ICON_CATALOG,
} from '@/entities/book';
import {
  Banknote,
  Beaker,
  Bookmark,
  BookOpenText,
  CalendarClock,
  Calculator,
  CloudSun,
  FilePenLine,
  FileText,
  Flag,
  FlaskConical,
  Gavel,
  LineChart,
  Microscope,
  MoonStar,
  NotebookTabs,
  ReceiptText,
  Scale,
  Star,
  Sun,
  University,
} from 'lucide-react';

const COVER_ICON_COMPONENTS: Record<BookCoverIconId, LucideIcon> = {
  'book-open-text': BookOpenText,
  'notebook-tabs': NotebookTabs,
  'file-pen-line': FilePenLine,
  'file-text': FileText,
  star: Star,
  bookmark: Bookmark,
  flag: Flag,
  sun: Sun,
  'moon-star': MoonStar,
  'cloud-sun': CloudSun,
  'calendar-clock': CalendarClock,
  'flask-conical': FlaskConical,
  microscope: Microscope,
  beaker: Beaker,
  banknote: Banknote,
  calculator: Calculator,
  scale: Scale,
  gavel: Gavel,
  'receipt-text': ReceiptText,
  'line-chart': LineChart,
  university: University,
};

export const BOOK_COVER_ICON_GROUP_LABELS: Record<BookCoverIconGroup, string> = {
  COMMON: '常用 / 文档',
  TIME: '时间 / 日常节奏',
  RESEARCH: '研究 / 实验 / 学术',
  FINANCE_LAW_AUDIT: '财务 / 法律 / 审计 / 指标',
};

export const BOOK_COVER_ICON_GROUP_ORDER: BookCoverIconGroup[] = [
  'COMMON',
  'TIME',
  'RESEARCH',
  'FINANCE_LAW_AUDIT',
];

export const getCoverIconMeta = (id?: BookCoverIconId | null): BookCoverIconMeta | undefined => {
  if (!id) return undefined;
  return BOOK_COVER_ICON_CATALOG.find((item) => item.id === id);
};

export const getCoverIconComponent = (id?: BookCoverIconId | null): LucideIcon | null => {
  if (!id) return null;
  return COVER_ICON_COMPONENTS[id] ?? null;
};

export const getGroupedCoverIconCatalog = (): Array<{
  group: BookCoverIconGroup;
  label: string;
  items: BookCoverIconMeta[];
}> => {
  return BOOK_COVER_ICON_GROUP_ORDER.map((group) => ({
    group,
    label: BOOK_COVER_ICON_GROUP_LABELS[group],
    items: BOOK_COVER_ICON_CATALOG.filter((item) => item.group === group),
  }));
};
