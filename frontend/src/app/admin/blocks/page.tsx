'use client';

import React from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Breadcrumb, Button } from '@/shared/ui';
import { useBook } from '@/features/book';
import { useBookshelf } from '@/features/bookshelf';
import { useLibrary } from '@/features/library';
import { useBlocks } from '@/features/block/model/hooks';
import { ChronicleTimelineList, useChronicleTimeline } from '@/features/chronicle';
import { BookDto, BookMaturity } from '@/entities/book';
import { ChronicleTimelinePage } from '@/entities/chronicle';
import { BookEditorRoot } from '@/modules/book-editor';
import { useI18n } from '@/i18n/useI18n';
import styles from './page.module.css';

const MATURITY_META: Record<BookMaturity, { label: string }> = {
  seed: { label: 'Seed · 草创' },
  growing: { label: 'Growing · 成长' },
  stable: { label: 'Stable · 稳定' },
  legacy: { label: 'Legacy · 归档' },
};

const STATUS_META: Record<BookDto['status'], { label: string; tone: 'draft' | 'published' | 'archived' | 'danger' }> = {
  DRAFT: { label: '草稿', tone: 'draft' },
  PUBLISHED: { label: '已发布', tone: 'published' },
  ARCHIVED: { label: '已归档', tone: 'archived' },
  DELETED: { label: '已删除', tone: 'danger' },
};

const TAB_DEFS = [
  { key: 'blocks', label: '块编辑' },
  { key: 'chronicle', label: '时间线' },
] as const;

type TabKey = (typeof TAB_DEFS)[number]['key'];

const TAB_STORAGE_PREFIX = 'wordloom.blocks.workspace.tab';

const formatRelativeTime = (iso?: string | null): string => {
  if (!iso) return '—';
  const target = new Date(iso).getTime();
  if (!Number.isFinite(target)) return '—';
  const diff = target - Date.now();
  const abs = Math.abs(diff);
  const table: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ['year', 1000 * 60 * 60 * 24 * 365],
    ['month', 1000 * 60 * 60 * 24 * 30],
    ['day', 1000 * 60 * 60 * 24],
    ['hour', 1000 * 60 * 60],
    ['minute', 1000 * 60],
    ['second', 1000],
  ];
  const rtf = new Intl.RelativeTimeFormat('zh-CN', { numeric: 'auto' });
  for (const [unit, value] of table) {
    if (abs >= value || unit === 'second') {
      return rtf.format(Math.round(diff / value), unit);
    }
  }
  return '—';
};

const deriveLifecycleTone = (status: BookDto['status']): 'active' | 'archived' => {
  if (status === 'ARCHIVED' || status === 'DELETED') {
    return 'archived';
  }
  return 'active';
};

const BlocksWorkspacePage: React.FC = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const bookId = searchParams.get('book_id') || '';
  const { t } = useI18n();

  const { data: book, isLoading: isBookLoading, error: bookError } = useBook(bookId);
  const { data: bookshelf } = useBookshelf(book?.bookshelf_id || '');
  const { data: library } = useLibrary(bookshelf?.library_id || '');

  const { data: blockList, isLoading: isBlocksLoading } = useBlocks(bookId);

  const { data: timelineData } = useChronicleTimeline(bookId, { pageSize: 15 });
  const timelinePages = React.useMemo(
    () => ((timelineData?.pages ?? []) as ChronicleTimelinePage[]),
    [timelineData],
  );
  const timelineEvents = React.useMemo(
    () => timelinePages.flatMap((timelinePage) => timelinePage.items),
    [timelinePages],
  );
  const chronicleTotal = timelinePages.length > 0 ? timelinePages[0].total : 0;
  const latestActivity = timelineEvents[0]?.occurred_at || book?.updated_at || book?.created_at;

  const totalBlocks = React.useMemo(() => {
    if (Array.isArray(blockList)) {
      return blockList.length;
    }
    return book?.block_count ?? 0;
  }, [blockList, book?.block_count]);

  const storageKey = React.useMemo(
    () => (bookId ? `${TAB_STORAGE_PREFIX}:${bookId}` : TAB_STORAGE_PREFIX),
    [bookId],
  );
  const [activeTab, setActiveTab] = React.useState<TabKey>('blocks');

  React.useEffect(() => {
    if (typeof window === 'undefined' || !storageKey) return;
    const saved = window.localStorage.getItem(storageKey) as TabKey | null;
    if (saved && TAB_DEFS.some((tab) => tab.key === saved)) {
      setActiveTab(saved);
    } else {
      setActiveTab('blocks');
    }
  }, [storageKey]);

  const handleTabChange = React.useCallback((key: TabKey) => {
    setActiveTab(key);
    if (typeof window !== 'undefined' && storageKey) {
      window.localStorage.setItem(storageKey, key);
    }
  }, [storageKey]);

  const metricsRows = React.useMemo(() => {
    const stablePlaceholder = '—';
    return [
      [
        { label: '块总数', value: String(totalBlocks ?? 0), hint: 'Blocks 总数（含分页）' },
        { label: 'Stable Blocks', value: stablePlaceholder, hint: '等待接入块成熟度统计' },
        { label: '覆盖率', value: stablePlaceholder, hint: 'Stable Blocks ÷ Blocks' },
      ],
      [
        {
          label: '最近活动',
          value: formatRelativeTime(latestActivity),
          hint: latestActivity ? new Date(latestActivity).toLocaleString('zh-CN', { hour12: false }) : '暂无事件',
        },
        { label: '本周查看', value: '—', hint: '尚未接入查看频次统计' },
        { label: '事件总数', value: String(chronicleTotal ?? 0), hint: 'Chronicle 事件总计（含分页）' },
      ],
    ];
  }, [chronicleTotal, latestActivity, totalBlocks]);

  if (!bookId) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <div className={styles.error}>
            <h2>缺少 book_id 参数</h2>
            <p>请从 Book 页面进入块工作台。</p>
            <button onClick={() => router.push('/admin/books')} className={styles.backButton}>
              返回
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isBookLoading || isBlocksLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <p>加载块工作台...</p>
        </div>
      </div>
    );
  }

  if (bookError || !book) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <div className={styles.error}>
            <h2>无法加载书籍</h2>
            <p>Book ID: {bookId}</p>
            <p>{bookError?.message || '未知错误'}</p>
            <button onClick={() => router.back()} className={styles.backButton}>
              返回
            </button>
          </div>
        </div>
      </div>
    );
  }

  const maturity = (book.maturity || 'seed') as BookMaturity;
  const maturityMeta = MATURITY_META[maturity];
  const statusMeta = STATUS_META[book.status];
  const lifecycleTone = deriveLifecycleTone(book.status);

  return (
    <div className={styles.page}>
      <div className={styles.inner}>
        <Breadcrumb
          items={[
            { label: t('bookshelves.library.breadcrumb.list'), href: '/admin/libraries' },
            library ? { label: library.name, href: `/admin/libraries/${library.id}` } : null,
            bookshelf ? { label: bookshelf.name, href: `/admin/bookshelves/${bookshelf.id}` } : null,
            book ? { label: book.title, href: `/admin/books/${book.id}` } : null,
            { label: '块工作台', active: true },
          ].filter(Boolean) as any}
        />

        <header className={styles.heroCard}>
          <div className={styles.heroHeader}>
            <div className={styles.titleGroup}>
              {(library?.name || bookshelf?.name) && (
                <span className={styles.superTitle}>
                  所属：{[bookshelf?.name, library?.name].filter(Boolean).join(' · ')}
                </span>
              )}
              <h1 className={styles.heroTitle}>{book.title}</h1>
              <p className={styles.heroSummary}>{book.summary || '暂无简介。'}</p>
            </div>
            <div className={styles.statusGroup}>
              <span className={styles.maturityPill} data-maturity={maturity}>{maturityMeta.label}</span>
              <span className={styles.statusPill} data-tone={statusMeta.tone}>{statusMeta.label}</span>
              <span className={styles.lifecyclePill} data-tone={lifecycleTone}>
                {lifecycleTone === 'active' ? 'Active' : 'Archived'}
              </span>
              <Button variant="secondary" size="sm" onClick={() => router.push(`/admin/books/${book.id}`)}>
                返回 Book 页面
              </Button>
            </div>
          </div>

          <div className={styles.heroMetrics}>
            {metricsRows.map((row, rowIndex) => (
              <div key={rowIndex} className={styles.metricRow}>
                {row.map((metric) => (
                  <div key={metric.label} className={styles.metric} title={metric.hint}>
                    <span className={styles.metricValue}>{metric.value}</span>
                    <span className={styles.metricLabel}>{metric.label}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </header>

        <div className={styles.layout}>
          <section className={styles.leftColumn}>
            <div className={styles.tabList} role="tablist" aria-label="Block 工作台视图切换">
              {TAB_DEFS.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab.key}
                  className={`${styles.tabButton} ${activeTab === tab.key ? styles.tabButtonActive : ''}`}
                  onClick={() => handleTabChange(tab.key)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className={styles.tabPanel}>
              {activeTab === 'blocks' && (
                <div className={styles.blocksTab}>
                  <BookEditorRoot bookId={bookId} />
                </div>
              )}

              {activeTab === 'chronicle' && (
                <div className={styles.chronicleTab}>
                  <ChronicleTimelineList bookId={bookId} />
                </div>
              )}
            </div>
          </section>

        </div>
      </div>
    </div>
  );
};

export default BlocksWorkspacePage;
