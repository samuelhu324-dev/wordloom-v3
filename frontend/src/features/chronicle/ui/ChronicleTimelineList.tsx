"use client";

import React from 'react';
import {
  BookOpenCheck,
  ArrowLeftRight,
  ArchiveRestore,
  Trash2,
  Undo2,
  Type,
  Sparkles,
  Eye,
  Layers,
  Clock3,
  LineChart,
  Gauge,
  CheckCircle2,
  RotateCcw,
  Palette,
  Camera,
  Flag,
  BookmarkPlus,
  ClipboardCheck,
  Tags,
  Timer,
  Activity,
  Image as ImageIcon,
} from 'lucide-react';
import { Button, Spinner } from '@/shared/ui';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import { ChronicleEventDto, ChronicleEventType, ChronicleTimelinePage } from '@/entities/chronicle';
import { CHRONICLE_DEFAULT_EVENT_TYPES, useChronicleTimeline } from '../model/hooks';
import styles from './ChronicleTimelineList.module.css';

type TranslateFn = (key: MessageKey, vars?: Record<string, string | number>) => string;

const STAGE_LABEL_KEYS: Record<string, MessageKey> = {
  seed: 'books.blocks.overview.stage.seed',
  growing: 'books.blocks.overview.stage.growing',
  stable: 'books.blocks.overview.stage.stable',
  legacy: 'books.blocks.overview.stage.legacy',
};

const STAGE_ORDER: Record<string, number> = {
  seed: 0,
  growing: 1,
  stable: 2,
  legacy: 3,
};

type StructureTaskSlug = 'longSummary' | 'tagLandscape' | 'outlineDepth' | 'todoZero';

const STRUCTURE_TASK_LABEL_KEYS: Record<StructureTaskSlug, MessageKey> = {
  longSummary: 'books.blocks.timeline.structureTasks.longSummary',
  tagLandscape: 'books.blocks.timeline.structureTasks.tagLandscape',
  outlineDepth: 'books.blocks.timeline.structureTasks.outlineDepth',
  todoZero: 'books.blocks.timeline.structureTasks.todoZero',
};

const STRUCTURE_TASK_TITLE_SYNONYMS: Record<StructureTaskSlug, string[]> = {
  longSummary: ['扩写摘要到 120 字', '扩写摘要到120字', 'Expand the summary to 120 characters'],
  tagLandscape: ['配置至少 3 个标签', '配置至少3个标签', 'Configure at least 3 tags'],
  outlineDepth: ['保持 15+ Blocks 且类型不少于 4 种', '保持15+ Blocks 且类型不少于4种', 'Maintain 15+ blocks with at least 4 types'],
  todoZero: ['清空关键 TODO', '清空关键TODO', 'Clear critical TODOs'],
};

const normalizeTaskTitle = (value: string) => value.replace(/\s+/g, ' ').trim().toLowerCase();

const STRUCTURE_TASK_TITLE_LOOKUP = new Map<string, StructureTaskSlug>();
Object.entries(STRUCTURE_TASK_TITLE_SYNONYMS).forEach(([slug, labels]) => {
  labels.forEach((label) => {
    STRUCTURE_TASK_TITLE_LOOKUP.set(normalizeTaskTitle(label), slug as StructureTaskSlug);
  });
});

const containsCjk = (value: string) => /[\u3400-\u9fff]/u.test(value);

const splitBilingualSegments = (value: string): string[] | null => {
  if (!value.includes('|') && !value.includes('\uFF5C')) {
    return null;
  }
  const segments = value
    .split(/[|\uFF5C]/g)
    .map((segment) => segment.trim())
    .filter(Boolean);
  return segments.length >= 2 ? segments : null;
};

const pickSegmentForLocale = (segments: string[], lang: string): string => {
  if (segments.length === 0) {
    return '';
  }
  const preferChinese = lang.startsWith('zh');
  if (preferChinese) {
    const candidate = segments.find((segment) => containsCjk(segment));
    if (candidate) {
      return candidate;
    }
  } else {
    const candidate = segments.find((segment) => !containsCjk(segment));
    if (candidate) {
      return candidate;
    }
  }
  return preferChinese ? segments[0] : segments[segments.length - 1];
};

const formatStructureTaskLabel = (slug: StructureTaskSlug | undefined, t: TranslateFn): string => {
  if (!slug) {
    return t('books.blocks.timeline.summary.structureTaskFallback');
  }
  const key = STRUCTURE_TASK_LABEL_KEYS[slug];
  return key ? t(key) : t('books.blocks.timeline.summary.structureTaskFallback');
};

const resolveStructureTaskTitle = (raw: unknown, lang: string, t: TranslateFn): string => {
  const fallback = t('books.blocks.timeline.summary.structureTaskFallback');
  if (typeof raw !== 'string') {
    return fallback;
  }
  const trimmed = raw.trim();
  if (!trimmed) {
    return fallback;
  }

  const bilingualSegments = splitBilingualSegments(trimmed);
  if (bilingualSegments) {
    const localizedSegment = pickSegmentForLocale(bilingualSegments, lang);
    if (localizedSegment) {
      const slug = STRUCTURE_TASK_TITLE_LOOKUP.get(normalizeTaskTitle(localizedSegment));
      if (slug) {
        return formatStructureTaskLabel(slug, t);
      }
      return localizedSegment;
    }
  }

  const slug = STRUCTURE_TASK_TITLE_LOOKUP.get(normalizeTaskTitle(trimmed));
  if (slug) {
    return formatStructureTaskLabel(slug, t);
  }

  return trimmed;
};

const EVENT_LABEL_KEYS: Record<ChronicleEventType, MessageKey> = {
  book_created: 'books.blocks.timeline.events.bookCreated',
  book_moved: 'books.blocks.timeline.events.bookMoved',
  book_moved_to_basement: 'books.blocks.timeline.events.bookMovedToBasement',
  book_soft_deleted: 'books.blocks.timeline.events.bookSoftDeleted',
  book_restored: 'books.blocks.timeline.events.bookRestored',
  book_deleted: 'books.blocks.timeline.events.bookDeleted',
  book_renamed: 'books.blocks.timeline.events.bookRenamed',
  book_updated: 'books.blocks.timeline.events.bookUpdated',
  block_created: 'books.blocks.timeline.events.blockCreated',
  block_updated: 'books.blocks.timeline.events.blockUpdated',
  block_soft_deleted: 'books.blocks.timeline.events.blockSoftDeleted',
  block_restored: 'books.blocks.timeline.events.blockRestored',
  block_type_changed: 'books.blocks.timeline.events.blockTypeChanged',
  block_status_changed: 'books.blocks.timeline.events.blockStatusChanged',
  book_opened: 'books.blocks.timeline.events.bookOpened',
  book_viewed: 'books.blocks.timeline.events.bookViewed',
  book_stage_changed: 'books.blocks.timeline.events.stageChanged',
  book_maturity_recomputed: 'books.blocks.timeline.events.maturityRecomputed',
  structure_task_completed: 'books.blocks.timeline.events.structureTaskCompleted',
  structure_task_regressed: 'books.blocks.timeline.events.structureTaskRegressed',
  cover_changed: 'books.blocks.timeline.events.coverChanged',
  cover_color_changed: 'books.blocks.timeline.events.coverColorChanged',
  content_snapshot_taken: 'books.blocks.timeline.events.snapshotTaken',
  wordcount_milestone_reached: 'books.blocks.timeline.events.wordcountMilestone',
  todo_promoted_from_block: 'books.blocks.timeline.events.todoPromoted',
  todo_completed: 'books.blocks.timeline.events.todoCompleted',
  tag_added_to_book: 'books.blocks.timeline.events.tagAddedToBook',
  tag_removed_from_book: 'books.blocks.timeline.events.tagRemovedFromBook',
  work_session_summary: 'books.blocks.timeline.events.workSession',
  focus_started: 'books.blocks.timeline.events.focusStarted',
  focus_ended: 'books.blocks.timeline.events.focusEnded',
};

const ICONS: Record<ChronicleEventType, React.ReactElement> = {
  book_created: <BookOpenCheck size={18} />,
  book_moved: <ArrowLeftRight size={18} />,
  book_moved_to_basement: <Trash2 size={18} />,
  book_soft_deleted: <Trash2 size={18} />,
  book_restored: <ArchiveRestore size={18} />,
  book_deleted: <Undo2 size={18} />, // logical delete record
  book_renamed: <Type size={18} />,
  book_updated: <Sparkles size={18} />,
  block_created: <Layers size={18} />,
  block_updated: <Sparkles size={18} />,
  block_soft_deleted: <Trash2 size={18} />,
  block_restored: <ArchiveRestore size={18} />,
  block_type_changed: <Layers size={18} />,
  block_status_changed: <Layers size={18} />,
  book_opened: <Eye size={18} />,
  book_viewed: <Eye size={18} />,
  book_stage_changed: <LineChart size={18} />,
  book_maturity_recomputed: <Gauge size={18} />,
  structure_task_completed: <CheckCircle2 size={18} />,
  structure_task_regressed: <RotateCcw size={18} />,
  cover_changed: <ImageIcon size={18} />,
  cover_color_changed: <Palette size={18} />,
  content_snapshot_taken: <Camera size={18} />,
  wordcount_milestone_reached: <Flag size={18} />,
  todo_promoted_from_block: <BookmarkPlus size={18} />,
  todo_completed: <ClipboardCheck size={18} />,
  tag_added_to_book: <Tags size={18} />,
  tag_removed_from_book: <Tags size={18} />,
  work_session_summary: <Timer size={18} />,
  focus_started: <Activity size={18} />,
  focus_ended: <Activity size={18} />,
};

const formatStageLabel = (value: unknown, t: TranslateFn, fallback: string): string => {
  if (typeof value !== 'string' || value.length === 0) {
    return fallback;
  }
  const key = STAGE_LABEL_KEYS[value.toLowerCase()];
  if (key) {
    return t(key);
  }
  return value;
};

const shortId = (value: unknown, fallback: string): string => {
  if (typeof value !== 'string' || value.length === 0) {
    return fallback;
  }
  return value.slice(0, 8);
};

const formatSignedNumber = (value: number) => (value > 0 ? `+${value}` : `${value}`);

const toNumber = (value: unknown): number | null => {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const getStageChangeLabel = (event: ChronicleEventDto, t: TranslateFn): string => {
  const payload = (event.payload || {}) as Record<string, unknown>;
  const from = String(payload.from || '').toLowerCase();
  const to = String(payload.to || '').toLowerCase();
  const fromOrder = STAGE_ORDER[from];
  const toOrder = STAGE_ORDER[to];

  if (typeof fromOrder === 'number' && typeof toOrder === 'number') {
    if (toOrder > fromOrder) {
      return t('books.blocks.timeline.events.stageUp');
    }
    if (toOrder < fromOrder) {
      return t('books.blocks.timeline.events.stageDown');
    }
  }
  return t(EVENT_LABEL_KEYS.book_stage_changed);
};

const getEventLabel = (event: ChronicleEventDto, t: TranslateFn): string => {
  if (event.event_type === 'book_stage_changed') {
    return getStageChangeLabel(event, t);
  }
  const key = EVENT_LABEL_KEYS[event.event_type];
  if (key) {
    return t(key);
  }
  return event.event_type;
};

const formatRelativeTime = (iso: string, lang: string): string => {
  const date = new Date(iso);
  const diffMs = date.getTime() - Date.now();
  const absMs = Math.abs(diffMs);
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['year', 1000 * 60 * 60 * 24 * 365],
    ['month', 1000 * 60 * 60 * 24 * 30],
    ['day', 1000 * 60 * 60 * 24],
    ['hour', 1000 * 60 * 60],
    ['minute', 1000 * 60],
    ['second', 1000],
  ];
  const rtf = new Intl.RelativeTimeFormat(lang || 'en-US', { numeric: 'auto' });
  for (const [unit, ms] of units) {
    if (absMs >= ms || unit === 'second') {
      const value = Math.round(diffMs / ms);
      return rtf.format(value, unit);
    }
  }
  return '';
};

const summarizePayload = (event: ChronicleEventDto, t: TranslateFn, lang: string): string => {
  const payload = (event.payload || {}) as Record<string, unknown>;
  const read = (key: string) => payload[key];
  const missing = t('books.blocks.timeline.summary.missing');
  const locale = lang || 'en-US';
  const separator = t('books.blocks.timeline.summary.separator');
  const defaultLabel = t('books.blocks.timeline.summary.placeholder.default');
  const formatNumberLocale = (value: number | null) => {
    if (value === null) return missing;
    return value.toLocaleString(locale);
  };
  const formatTrigger = (value: unknown) =>
    typeof value === 'string' && value.trim().length > 0
      ? t('books.blocks.timeline.summary.fragment.trigger', { trigger: value })
      : '';
  const formatPoints = (value: number | null, variant: 'bonus' | 'plain') => {
    if (value === null) return '';
    if (variant === 'bonus') {
      return t('books.blocks.timeline.summary.fragment.pointsAwarded', { points: Math.abs(value) });
    }
    return t('books.blocks.timeline.summary.fragment.pointsPlain', { points: formatSignedNumber(value) });
  };

  switch (event.event_type) {
    case 'book_moved':
      return t('books.blocks.timeline.summary.bookMoved', {
        from: shortId(read('from_bookshelf_id'), missing),
        to: shortId(read('to_bookshelf_id'), missing),
      });
    case 'book_moved_to_basement':
    case 'book_soft_deleted':
      return t('books.blocks.timeline.summary.bookMovedToBasement', {
        from: shortId(read('from_bookshelf_id'), missing),
        to: shortId(read('basement_bookshelf_id'), missing),
      });
    case 'book_restored':
      return t('books.blocks.timeline.summary.bookRestored', {
        destination: shortId(read('restored_to_bookshelf_id'), missing),
      });
    case 'book_deleted':
      return t('books.blocks.timeline.summary.bookDeleted', {
        bookshelf: shortId(read('bookshelf_id'), missing),
      });
    case 'block_status_changed':
      return t('books.blocks.timeline.summary.blockStatusChanged', {
        old: typeof read('old_status') === 'string' ? String(read('old_status')) : missing,
        next: typeof read('new_status') === 'string' ? String(read('new_status')) : missing,
      });
    case 'book_opened':
    case 'book_viewed': {
      const actor = typeof event.actor_id === 'string' && event.actor_id ? event.actor_id.slice(0, 8) : '';
      return actor
        ? t('books.blocks.timeline.summary.bookVisit', { actor })
        : t('books.blocks.timeline.summary.bookVisitFallback');
    }
    case 'cover_changed': {
      const fromIcon = typeof read('from_icon') === 'string' ? String(read('from_icon')) || defaultLabel : defaultLabel;
      const toIcon = typeof read('to_icon') === 'string' ? String(read('to_icon')) || defaultLabel : defaultLabel;
      const mediaId = read('media_id');
      const triggerFragment = formatTrigger(read('trigger'));
      const mediaFragment = typeof mediaId === 'string' && mediaId
        ? t('books.blocks.timeline.summary.fragment.media', { id: shortId(mediaId, missing) })
        : '';
      return `${t('books.blocks.timeline.summary.coverChanged', { from: fromIcon, to: toIcon })}${mediaFragment}${triggerFragment}`;
    }
    case 'cover_color_changed': {
      const fromColor = typeof read('from_color') === 'string' ? String(read('from_color')) || defaultLabel : defaultLabel;
      const toColor = typeof read('to_color') === 'string' ? String(read('to_color')) || defaultLabel : defaultLabel;
      const paletteRaw = read('palette');
      const palette = Array.isArray(paletteRaw)
        ? (paletteRaw as unknown[])
            .map((entry) => String(entry))
            .filter((entry) => entry.length > 0)
            .slice(0, 3)
        : [];
      const paletteFragment = palette.length
        ? t('books.blocks.timeline.summary.fragment.palette', { colors: palette.join(', ') })
        : '';
      const triggerFragment = formatTrigger(read('trigger'));
      return `${t('books.blocks.timeline.summary.coverColorChanged', { from: fromColor, to: toColor })}${paletteFragment}${triggerFragment}`;
    }
    case 'book_stage_changed': {
      const fromLabel = formatStageLabel(read('from'), t, missing);
      const toLabel = formatStageLabel(read('to'), t, missing);
      const scoreFragment = (() => {
        const score = toNumber(read('score'));
        if (score === null) return '';
        return t('books.blocks.timeline.summary.fragment.score', { score });
      })();
      const triggerFragment = formatTrigger(read('trigger'));
      const manualFragment = read('manual_override') ? t('books.blocks.timeline.summary.fragment.manual') : '';
      return `${t('books.blocks.timeline.summary.stageChanged', { from: fromLabel, to: toLabel })}${scoreFragment}${triggerFragment}${manualFragment}`;
    }
    case 'book_maturity_recomputed': {
      const previousScore = toNumber(read('previous_score'));
      const newScore = toNumber(read('new_score'));
      const deltaFragment = (() => {
        const delta = toNumber(read('delta'));
        if (delta === null || delta === 0) return '';
        return t('books.blocks.timeline.summary.fragment.delta', { delta: formatSignedNumber(delta) });
      })();
      const stageFragment = (() => {
        const stage = read('stage');
        if (typeof stage !== 'string' || stage.length === 0) return '';
        return t('books.blocks.timeline.summary.fragment.stage', {
          stage: formatStageLabel(stage, t, missing),
        });
      })();
      const triggerFragment = formatTrigger(read('trigger'));
      const initialFragment = read('initial') ? t('books.blocks.timeline.summary.fragment.initial') : '';
      return `${t('books.blocks.timeline.summary.maturityRecomputed', {
        previous: previousScore !== null ? previousScore : missing,
        next: newScore !== null ? newScore : missing,
      })}${deltaFragment}${stageFragment}${triggerFragment}${initialFragment}`;
    }
    case 'structure_task_completed': {
      const title = resolveStructureTaskTitle(read('title'), lang, t);
      const stageFragment = (() => {
        const stage = read('stage');
        if (typeof stage !== 'string' || stage.length === 0) return '';
        return t('books.blocks.timeline.summary.fragment.stage', {
          stage: formatStageLabel(stage, t, missing),
        });
      })();
      const triggerFragment = formatTrigger(read('trigger'));
      return `${t('books.blocks.timeline.summary.structureTaskCompleted', { title })}${formatPoints(toNumber(read('points')), 'bonus')}${stageFragment}${triggerFragment}`;
    }
    case 'structure_task_regressed': {
      const title = resolveStructureTaskTitle(read('title'), lang, t);
      const stageFragment = (() => {
        const stage = read('stage');
        if (typeof stage !== 'string' || stage.length === 0) return '';
        return t('books.blocks.timeline.summary.fragment.stage', {
          stage: formatStageLabel(stage, t, missing),
        });
      })();
      const triggerFragment = formatTrigger(read('trigger'));
      return `${t('books.blocks.timeline.summary.structureTaskRegressed', { title })}${formatPoints(toNumber(read('points')), 'plain')}${stageFragment}${triggerFragment}`;
    }
    case 'content_snapshot_taken': {
      const blockCount = toNumber(read('block_count'));
      const wordCount = toNumber(read('total_word_count'));
      const typeCounts = read('block_type_counts');
      const typeCount =
        typeCounts && typeof typeCounts === 'object'
          ? Object.keys(typeCounts as Record<string, unknown>).length
          : 0;
      const parts = [
        blockCount !== null ? t('books.blocks.timeline.summary.fragment.blocks', { count: blockCount }) : '',
        typeCount ? t('books.blocks.timeline.summary.fragment.types', { count: typeCount }) : '',
        wordCount !== null
          ? t('books.blocks.timeline.summary.fragment.words', { count: wordCount.toLocaleString(locale) })
          : '',
      ].filter(Boolean);
      const metrics = parts.length ? parts.join(separator) : missing;
      const triggerFragment = formatTrigger(read('trigger'));
      return `${metrics}${triggerFragment}`;
    }
    case 'wordcount_milestone_reached': {
      const milestone = toNumber(read('milestone'));
      const total = toNumber(read('total_word_count'));
      const previous = toNumber(read('previous_word_count'));
      const deltaValue =
        total !== null && previous !== null ? total - previous : null;
      const deltaFragment = deltaValue !== null && deltaValue !== 0
        ? t('books.blocks.timeline.summary.fragment.deltaWords', { delta: formatSignedNumber(deltaValue) })
        : '';
      const totalFragment = total !== null
        ? t('books.blocks.timeline.summary.fragment.totalWords', { count: formatNumberLocale(total) })
        : '';
      return `${t('books.blocks.timeline.summary.wordcountMilestone', {
        milestone: milestone !== null ? formatNumberLocale(milestone) : missing,
      })}${deltaFragment}${totalFragment}`;
    }
    case 'todo_promoted_from_block': {
      const text = typeof read('text') === 'string' && read('text')
        ? String(read('text'))
        : t('books.blocks.timeline.summary.todoFallback');
      const todoId = read('todo_id');
      const todoFragment = typeof todoId === 'string' && todoId ? `#${shortId(todoId, missing)}` : '';
      const blockFragment = read('block_id')
        ? t('books.blocks.timeline.summary.fragment.block', { block: shortId(String(read('block_id')), missing) })
        : '';
      const urgentFragment = read('is_urgent') ? t('books.blocks.timeline.summary.fragment.urgent') : '';
      return `${t('books.blocks.timeline.summary.todoPromoted', { text, todo: todoFragment })}${blockFragment}${urgentFragment}`;
    }
    case 'todo_completed': {
      const text = typeof read('text') === 'string' && read('text')
        ? String(read('text'))
        : t('books.blocks.timeline.summary.todoFallback');
      const blockFragment = read('block_id')
        ? t('books.blocks.timeline.summary.fragment.block', { block: shortId(String(read('block_id')), missing) })
        : '';
      const promotedFragment = read('promoted') ? t('books.blocks.timeline.summary.fragment.promoted') : '';
      return `${t('books.blocks.timeline.summary.todoCompleted', { text })}${blockFragment}${promotedFragment}`;
    }
    case 'work_session_summary': {
      const duration = toNumber(read('duration_seconds'));
      const blocks = toNumber(read('blocks_touched'));
      const wordDelta = toNumber(read('word_delta'));
      const minutes = duration !== null ? Math.round(duration / 60) : null;
      const durationFragment = duration !== null
        ? minutes && minutes >= 1
          ? t('books.blocks.timeline.summary.fragment.durationMinutes', { value: minutes })
          : t('books.blocks.timeline.summary.fragment.durationSeconds', { value: duration })
        : '';
      const blocksFragment = blocks !== null
        ? t('books.blocks.timeline.summary.fragment.blocksTouched', { count: blocks })
        : '';
      const wordsFragment = wordDelta !== null && wordDelta !== 0
        ? t('books.blocks.timeline.summary.fragment.wordDelta', { value: formatSignedNumber(wordDelta) })
        : '';
      const parts = [durationFragment, blocksFragment, wordsFragment].filter(Boolean);
      return parts.length ? parts.join(separator) : missing;
    }
    case 'focus_started':
    case 'focus_ended':
      return '';
    default:
      return missing;
  }
};

interface ChronicleTimelineListProps {
  bookId: string;
  title?: string;
  subtitle?: string;
  variant?: 'standalone' | 'embedded';
  pageSize?: number;
  maxListHeight?: number;
}

export const ChronicleTimelineList: React.FC<ChronicleTimelineListProps> = ({
  bookId,
  title,
  subtitle,
  variant = 'standalone',
  pageSize = 15,
  maxListHeight,
}) => {
  const { t, lang } = useI18n();
  const locale = lang || 'en-US';
  const [showVisits, setShowVisits] = React.useState(false);
  const eventTypes = React.useMemo(
    () => (showVisits ? undefined : CHRONICLE_DEFAULT_EVENT_TYPES),
    [showVisits]
  );

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
  } = useChronicleTimeline(bookId, { pageSize, eventTypes });

  const events = React.useMemo<ChronicleEventDto[]>(() => {
    const pages = (data?.pages ?? []) as ChronicleTimelinePage[];
    return pages.flatMap((page) => page.items);
  }, [data]);

  const cardClassName = variant === 'embedded'
    ? `${styles.timelineCard} ${styles.timelineEmbedded}`
    : styles.timelineCard;

  const headerTitle = title ?? t('books.blocks.timeline.title');
  const headerSubtitle = subtitle ?? t('books.blocks.timeline.subtitle');
  const toggleLabel = t('books.blocks.timeline.toggleVisits');

  return (
    <section className={cardClassName} aria-label={headerTitle}>
      {(headerTitle || headerSubtitle) && (
        <header className={styles.timelineHeader}>
          <div>
            {headerTitle && <h3>{headerTitle}</h3>}
            {headerSubtitle && <p>{headerSubtitle}</p>}
          </div>
          <label className={styles.toggle}>
            <input
              type="checkbox"
              checked={showVisits}
              onChange={(event) => setShowVisits(event.target.checked)}
            />
            <span>{toggleLabel}</span>
          </label>
        </header>
      )}

      {isLoading ? (
        <div className={styles.state}>
          <Spinner size="md" />
          <span>{t('books.blocks.timeline.state.loading')}</span>
        </div>
      ) : isError ? (
        <div className={styles.state}>
          <p>{t('books.blocks.timeline.state.error')}</p>
          <Button variant="secondary" size="sm" onClick={() => refetch()}>
            {t('books.blocks.timeline.actions.retry')}
          </Button>
        </div>
      ) : events.length === 0 ? (
        <div className={styles.state}>
          <Clock3 size={18} />
          <p>{t('books.blocks.timeline.state.empty')}</p>
        </div>
      ) : (
        <ul
          className={styles.timelineList}
          style={typeof maxListHeight === 'number' ? { maxHeight: maxListHeight } : undefined}
        >
          {events.map((event) => {
            const summary = summarizePayload(event, t, locale);
            return (
              <li key={event.id} className={styles.timelineItem}>
              <span className={styles.iconWrapper}>{ICONS[event.event_type] || <Clock3 size={18} />}</span>
              <div className={styles.itemContent}>
                <div className={styles.itemHeader}>
                  <strong>{getEventLabel(event, t)}</strong>
                  <span
                    className={styles.time}
                    title={new Date(event.occurred_at).toLocaleString(locale)}
                  >
                    {formatRelativeTime(event.occurred_at, locale)}
                  </span>
                </div>
                {summary && <p className={styles.summary}>{summary}</p>}
                {event.actor_id && (
                  <p className={styles.actor}>
                    {t('books.blocks.timeline.actor', { id: event.actor_id.slice(0, 8) })}
                  </p>
                )}
              </div>
            </li>
            );
          })}
        </ul>
      )}

      {false && events.length > 0 && hasNextPage && (
        <div className={styles.footer}>
          <Button
            variant="secondary"
            size="sm"
            loading={isFetchingNextPage}
            onClick={() => fetchNextPage()}
            fullWidth
          >
            {t('books.blocks.timeline.actions.loadMore')}
          </Button>
        </div>
      )}
    </section>
  );
};

ChronicleTimelineList.displayName = 'ChronicleTimelineList';
