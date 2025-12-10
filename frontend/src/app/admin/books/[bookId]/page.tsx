"use client";

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useQueryClient } from '@tanstack/react-query';
import { Breadcrumb, Button } from '@/shared/ui';
import { useBook } from '@/features/book';
import { useRecalculateBookMaturity } from '@/features/book/model/hooks';
import { useBookshelf } from '@/features/bookshelf';
import { useLibrary } from '@/features/library';
import { ChronicleTimelineList, useRecentChronicleEvents, CHRONICLE_QUERY_KEY } from '@/features/chronicle';
import {
  useBlocks,
  useUpdateBlockContentMutation,
} from '@/features/block/model/hooks';
import { BookMaturity } from '@/entities/book';
import { TodoListBlockContent, serializeBlockContent } from '@/entities/block';
import { showToast } from '@/shared/ui/toast';
import { extractPromotedTodosFromBlocks } from '@/features/block/lib/promotedTodos';
import { NextStepsChecklist } from '@/features/book/ui/NextStepsChecklist';
import { formatRelativeTime as formatBookRelativeTime } from '@/features/book/ui/bookVisuals';
import { useLatestBookMaturitySnapshot, MATURITY_QUERY_KEY } from '@/features/maturity';
import type { TransitionTaskDto, MaturityScoreComponentDto } from '@/features/maturity';
import { MaturityScoreBreakdown } from '@/features/maturity/ui/MaturityScoreBreakdown';
import { BookEditorRoot } from '@/modules/book-editor';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import styles from './page.module.css';

const TAB_KEYS = ['overview', 'blocks', 'timeline'] as const;

type TabKey = (typeof TAB_KEYS)[number];

const isTabKey = (value: string | null): value is TabKey => Boolean(value && TAB_KEYS.includes(value as TabKey));

const TAB_STORAGE_PREFIX = 'wordloom.book.detail.tab';

const clampScore = (value?: number | null): number => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  return Math.min(100, Math.max(0, Math.round(value)));
};

type ScoreGroupKey = 'structure' | 'activity' | 'quality' | 'task' | 'manual' | 'other';

type TranslateFn = (key: MessageKey, vars?: Record<string, string | number>) => string;

const resolveScoreGroup = (factor?: string | null): ScoreGroupKey => {
  const source = factor || '';
  if (source.startsWith('structure_')) return 'structure';
  if (source.startsWith('activity_')) return 'activity';
  if (source.startsWith('quality_')) return 'quality';
  if (source.startsWith('task_')) return 'task';
  if (source === 'manual_adjustment') return 'manual';
  return 'other';
};

const summarizeScoreComponents = (components: MaturityScoreComponentDto[], t: TranslateFn): string => {
  if (!Array.isArray(components) || components.length === 0) {
    return t('books.blocks.overview.score.empty');
  }
  const totals = new Map<ScoreGroupKey, number>();
  components.forEach((component) => {
    const key = resolveScoreGroup(component.factor);
    const points = typeof component.points === 'number' ? component.points : 0;
    const next = (totals.get(key) ?? 0) + points;
    totals.set(key, next);
  });
  const parts = Array.from(totals.entries())
    .filter(([, points]) => points !== 0)
    .map(([key, points]) => {
      const label = t(`books.blocks.overview.score.groups.${key}` as MessageKey);
      return `${label} ${points > 0 ? `+${points}` : points}`;
    });
  return parts.length > 0 ? parts.join(' + ') : t('books.blocks.overview.score.empty');
};

const formatSnapshotTimestamp = (value?: string | null, locale: string = 'zh-CN'): string => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString(locale, { hour12: false });
};

export default function BookDetailPage() {
  const params = useParams();
  const router = useRouter();
  const bookId = (params.bookId as string) || '';
  const queryClient = useQueryClient();
  const { t, lang } = useI18n();

  const {
    data: book,
    isLoading: isBookLoading,
    error: bookError,
  } = useBook(bookId);
  const {
    data: maturitySnapshot,
    isLoading: isMaturitySnapshotLoading,
  } = useLatestBookMaturitySnapshot(bookId);
  const recalcMaturity = useRecalculateBookMaturity(bookId);
  const refreshPlan104Data = React.useCallback(async () => {
    if (!bookId) return;
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: MATURITY_QUERY_KEY.root }),
      queryClient.invalidateQueries({ queryKey: CHRONICLE_QUERY_KEY.all }),
    ]);
  }, [bookId, queryClient]);

  const {
    data: bookshelf,
  } = useBookshelf(book?.bookshelf_id || '');

  const {
    data: library,
  } = useLibrary(bookshelf?.library_id || '');

  const tabDefs = React.useMemo(
    () => TAB_KEYS.map((key) => ({ key, label: t(`books.blocks.tabs.${key}` as MessageKey) })),
    [t]
  );

  const storageKey = React.useMemo(
    () => (bookId ? `${TAB_STORAGE_PREFIX}:${bookId}` : TAB_STORAGE_PREFIX),
    [bookId]
  );
  const [activeTab, setActiveTab] = React.useState<TabKey>('overview');

  React.useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem(storageKey) as TabKey | null;
    if (isTabKey(saved)) {
      setActiveTab(saved);
    } else {
      setActiveTab('overview');
    }
  }, [storageKey]);

  const handleTabChange = React.useCallback((key: TabKey) => {
    setActiveTab(key);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(storageKey, key);
    }
  }, [storageKey]);

  const { data: fullBlockList, isLoading: isBlocksLoading } = useBlocks(bookId);
  const updateBlockContent = useUpdateBlockContentMutation();
  const totalBlocks = React.useMemo(() => {
    if (Array.isArray(fullBlockList) && fullBlockList.length > 0) {
      return fullBlockList.length;
    }
    return book?.block_count ?? 0;
  }, [book?.block_count, fullBlockList]);

  const { data: recentChronicle } = useRecentChronicleEvents(bookId);
  const chronicleTotal = recentChronicle?.total ?? 0;
  const latestChronicle = recentChronicle?.items?.[0]?.occurred_at;

  const overviewStats = React.useMemo(() => {
    const placeholder = t('books.blocks.shared.emDash');
    const snapshotStage = (maturitySnapshot?.stage ?? 'seed') as BookMaturity;
    const stageLabel = t(`books.blocks.overview.stage.${snapshotStage}` as MessageKey);
    const manualOverride = Boolean(maturitySnapshot?.manualOverride);
    const manualReason = (maturitySnapshot?.manualReason || '').trim();
    const baseNarrative = t(`books.blocks.overview.stage.${snapshotStage}.description` as MessageKey);
    const stageDescription = manualOverride
      ? manualReason
        ? t('books.blocks.overview.stage.manualLockWithReason', { description: baseNarrative, reason: manualReason })
        : t('books.blocks.overview.stage.manualLock', { description: baseNarrative })
      : baseNarrative;
    const coverage = clampScore(maturitySnapshot?.score.value ?? null);
    const snapshotCreated = maturitySnapshot?.createdAt;
    const snapshotRelative = snapshotCreated ? formatBookRelativeTime(snapshotCreated, lang) : placeholder;
    const snapshotAbsolute = snapshotCreated
      ? formatSnapshotTimestamp(snapshotCreated, lang) || t('books.blocks.overview.snapshot.none')
      : t('books.blocks.overview.snapshot.none');
    const latestActivityLabel = latestChronicle
      ? formatBookRelativeTime(latestChronicle, lang)
      : t('books.blocks.overview.activity.none');
    const latestActivityHint = latestChronicle
      ? new Date(latestChronicle).toLocaleString(lang, { hour12: false })
      : t('books.blocks.overview.activity.none');
    const rawComponents = maturitySnapshot?.score?.components;
    const scoreComponents = Array.isArray(rawComponents) ? rawComponents : [];
    const manualAdjustmentPoints = scoreComponents.reduce((sum, component) => {
      if (component.factor === 'manual_adjustment' && typeof component.points === 'number') {
        return sum + component.points;
      }
      return sum;
    }, 0);
    const roundedManualBonus = Math.round(manualAdjustmentPoints);
    const snapshotOperationsBonus = Number.isFinite(maturitySnapshot?.operationsBonus)
      ? Math.round(maturitySnapshot?.operationsBonus ?? 0)
      : 0;
    const operationsBonus = roundedManualBonus !== 0 ? roundedManualBonus : snapshotOperationsBonus;
    const baseScore = clampScore(coverage - operationsBonus);
    const scoreSummary = summarizeScoreComponents(scoreComponents, t);

    return {
      coverage,
      stageLabel,
      stageDescription,
      stageKey: snapshotStage,
      scoreValue: coverage,
      baseScore,
      operationsBonus,
      scoreSummary,
      scoreComponents,
      usageBlocks: totalBlocks ?? 0,
      usageEvents: chronicleTotal ?? 0,
      latestActivityLabel,
      latestActivityHint,
      snapshotRelative,
      snapshotAbsolute,
    } as const;
  }, [chronicleTotal, latestChronicle, maturitySnapshot, totalBlocks, lang, t]);
  const currentOperationsBonus = overviewStats?.operationsBonus ?? 0;

  const structureSummary = React.useMemo(() => {
    if (!maturitySnapshot) {
      return null;
    }
    const tasks = Array.isArray(maturitySnapshot.tasks)
      ? (maturitySnapshot.tasks as TransitionTaskDto[])
      : [];
    let completed = 0;
    let active = 0;
    tasks.forEach((task) => {
      if (task.status === 'completed') {
        completed += 1;
        return;
      }
      if (task.status !== 'locked') {
        active += 1;
      }
    });
    const stage = maturitySnapshot.stage as BookMaturity;
    return {
      stageLabel: t(`books.blocks.overview.stage.${stage}` as MessageKey) ?? stage,
      completed,
      total: tasks.length,
      active,
      snapshotLabel: formatSnapshotTimestamp(maturitySnapshot.createdAt, lang),
    } as const;
  }, [lang, maturitySnapshot, t]);

  const promotedTodos = React.useMemo(
    () => extractPromotedTodosFromBlocks(fullBlockList ?? []),
    [fullBlockList]
  );

  type InsightView = 'score' | 'tasks' | 'todos';
  const [insightsView, setInsightsView] = React.useState<InsightView>('score');
  const [isBonusDialogOpen, setIsBonusDialogOpen] = React.useState(false);
  const [bonusInput, setBonusInput] = React.useState('');
  const [bonusSubmitting, setBonusSubmitting] = React.useState(false);
  const [bonusError, setBonusError] = React.useState<string | null>(null);
  const bonusInputId = React.useId();

  const insightViewDefs = React.useMemo(
    () => [
      { key: 'score' as InsightView, label: t('books.blocks.overview.insights.tabs.score') },
      {
        key: 'tasks' as InsightView,
        label: structureSummary
          ? t('books.blocks.overview.insights.tabs.tasks', {
              completed: structureSummary.completed,
              total: structureSummary.total,
            })
          : t('books.blocks.overview.insights.tabs.tasksFallback'),
      },
      {
        key: 'todos' as InsightView,
        label: promotedTodos.length
          ? t('books.blocks.overview.insights.tabs.todos', { count: promotedTodos.length })
          : t('books.blocks.overview.insights.tabs.todosFallback'),
      },
    ],
    [promotedTodos.length, structureSummary, t]
  );

  const [pendingTodoKey, setPendingTodoKey] = React.useState<string | null>(null);

  const handleTogglePromotedTodo = React.useCallback(async (blockId: string, itemId: string, checked: boolean) => {
    if (!fullBlockList) return;
    const targetBlock = fullBlockList.find((candidate) => candidate.id === blockId);
    if (!targetBlock || targetBlock.kind !== 'todo_list') {
      return;
    }
    const source = targetBlock.content as TodoListBlockContent;
    const items = Array.isArray(source?.items) ? source.items : [];
    const nextItems = items.map((item) => (item.id === itemId ? { ...item, checked } : item));
    const nextContent: TodoListBlockContent = { ...source, items: nextItems };
    const mutationKey = `${blockId}:${itemId}`;
    setPendingTodoKey(mutationKey);
    try {
      await updateBlockContent.mutateAsync({
        blockId,
        content: serializeBlockContent(targetBlock.kind, nextContent),
      });
    } catch (error) {
      console.error('更新 Todo 失败', error);
      showToast(t('books.blocks.toast.todoUpdateFailed'));
    } finally {
      setPendingTodoKey((current) => (current === mutationKey ? null : current));
    }
  }, [fullBlockList, t, updateBlockContent]);

  const handleGlobalSave = React.useCallback(() => {
    showToast(t('books.blocks.toast.autosaveHint'));
  }, [t]);

  React.useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        handleGlobalSave();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleGlobalSave]);

  const handleBlockLifecycle = React.useCallback(async (type: 'created' | 'deleted') => {
    try {
      await recalcMaturity.mutateAsync({
        operations_bonus: currentOperationsBonus,
        trigger: type === 'created' ? 'block_created' : 'block_deleted',
      });
      await refreshPlan104Data();
    } catch (error) {
      console.warn(`块${type === 'created' ? '创建' : '删除'}后刷新成熟度失败`, error);
    }
  }, [currentOperationsBonus, recalcMaturity, refreshPlan104Data]);

  const handleAdjustBonus = React.useCallback(() => {
    setBonusInput(String(overviewStats?.operationsBonus ?? 0));
    setBonusError(null);
    setIsBonusDialogOpen(true);
  }, [overviewStats?.operationsBonus]);

  const handleCloseBonusDialog = React.useCallback(() => {
    if (bonusSubmitting) return;
    setIsBonusDialogOpen(false);
  }, [bonusSubmitting]);

  const handleSubmitBonusDialog = React.useCallback(async () => {
    const parsed = Number(bonusInput);
    if (!Number.isFinite(parsed)) {
      setBonusError(t('books.blocks.toast.opsBonusInvalid'));
      return;
    }
    const normalized = Math.round(parsed);
    if (normalized < -5 || normalized > 5) {
      setBonusError(t('books.blocks.toast.opsBonusInvalid'));
      return;
    }
    try {
      setBonusSubmitting(true);
      await recalcMaturity.mutateAsync({ operations_bonus: normalized, trigger: 'adjust_ops_bonus' });
      showToast(t('books.blocks.toast.opsBonusApplied'));
      setIsBonusDialogOpen(false);
      await refreshPlan104Data();
    } catch (error) {
      showToast(t('books.blocks.toast.opsBonusFailed'));
    } finally {
      setBonusSubmitting(false);
    }
  }, [bonusInput, recalcMaturity, refreshPlan104Data, t]);

  React.useEffect(() => {
    if (!isBonusDialogOpen) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        handleCloseBonusDialog();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [handleCloseBonusDialog, isBonusDialogOpen]);

  if (isBookLoading) {
    return (
      <div className={styles.page}>
        <div className={styles.inner}>
          <p>{t('books.blocks.shell.loading')}</p>
        </div>
      </div>
    );
  }

  if (bookError || !book) {
    return (
      <div className={styles.page}>
        <div className={styles.error}>
          <h2>{t('books.blocks.shell.error.title')}</h2>
          <p>{t('books.blocks.shell.error.bookId', { id: bookId })}</p>
          <p className={styles.errorMessage}>{bookError?.message || t('books.blocks.shell.error.unknown')}</p>
          <button onClick={() => router.back()} className={styles.backButton}>{t('books.blocks.shell.error.back')}</button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={styles.page}>
        <div className={styles.inner}>
          <Breadcrumb
            items={[
              { label: t('books.blocks.nav.libraries'), href: '/admin/libraries' },
              library ? { label: library.name, href: `/admin/libraries/${library.id}` } : null,
              bookshelf ? { label: bookshelf.name, href: `/admin/bookshelves/${bookshelf.id}` } : null,
              { label: book.title, active: true },
            ].filter(Boolean) as any}
          />

        <header className={styles.heroCard}>
          <div className={styles.heroIntro}>
            <div className={styles.heroHeader}>
              <div className={styles.titleGroup}>
                <h1 className={styles.heroTitle}>{book.title}</h1>
                <p className={styles.heroSummary}>{book.summary || t('books.blocks.hero.summary.empty')}</p>
              </div>
              <div className={styles.heroActions}>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={handleGlobalSave}
                  disabled={isBlocksLoading}
                >
                  {isBlocksLoading
                    ? t('books.blocks.hero.autoSave.loading')
                    : t('books.blocks.hero.autoSave.label')}
                </Button>
              </div>
            </div>
          </div>
        </header>

        <div className={styles.workspace}>
          <div className={styles.tabList} role="tablist" aria-label={t('books.blocks.tabs.aria')}>
            {tabDefs.map((tab) => (
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
            {activeTab === 'overview' && (
              <div className={styles.overview}>
                <section className={styles.mainColumn}>
                    <article className={`${styles.sectionCard} ${styles.metricsSectionCard}`}>
                      <section className={styles.metricsSummaryBar} aria-label={t('books.blocks.overview.metrics.aria')}>
                        <div className={styles.maturityTop}>
                          <div className={styles.maturityPrimary}>
                            <div className={styles.maturityHeading}>
                              <span className={styles.maturityEyebrow}>{t('books.blocks.overview.maturityEyebrow')}</span>
                              <span className={styles.maturityStageChip} data-stage={overviewStats.stageKey}>
                                {overviewStats.stageLabel?.toUpperCase()}
                              </span>
                            </div>
                            <div className={styles.maturityMeter}>
                              <div className={styles.metricsProgressTrack} aria-hidden="true">
                                <div
                                  className={styles.metricsProgressFill}
                                  style={{ width: `${overviewStats.coverage}%` }}
                                />
                              </div>
                              <div className={styles.maturityMeterStats}>
                                <span className={styles.maturityMeterValue}>{overviewStats.coverage}%</span>
                                <span className={styles.maturityScoreOperator}>=</span>
                                <span className={styles.maturityBaseValue}>{overviewStats.baseScore}%</span>
                                <span className={styles.maturityScoreOperator}>+</span>
                                <button
                                  type="button"
                                  className={styles.maturityBonusAdjust}
                                  onClick={handleAdjustBonus}
                                >
                                  {`${overviewStats.operationsBonus >= 0 ? '+' : ''}${overviewStats.operationsBonus}%`}
                                </button>
                              </div>
                            </div>
                            <p className={styles.maturityDescription}>{overviewStats.stageDescription}</p>
                          </div>
                        </div>

                        <div className={styles.coreCardsGrid}>
                          <section className={`${styles.coreCard} ${styles.scoreCard}`} aria-label={t('books.blocks.overview.score.aria')}>
                            <span className={styles.coreValue}>{overviewStats.scoreValue}</span>
                            <span className={styles.coreDivider} aria-hidden="true" />
                            <span className={styles.coreLabel}>{t('books.blocks.overview.score.label')}</span>
                            <span className={styles.coreMeta}>{overviewStats.scoreSummary}</span>
                          </section>

                          <section className={`${styles.coreCard} ${styles.usageCard}`} aria-label={t('books.blocks.overview.usage.aria')}>
                            <div className={styles.usageMetric}>
                              <span className={styles.coreValue}>{overviewStats.usageBlocks}</span>
                              <span className={styles.usageLabel}>{t('books.blocks.overview.usage.blocks')}</span>
                            </div>
                            <div className={styles.usageMetric}>
                              <span className={styles.coreValue}>{overviewStats.usageEvents}</span>
                              <span className={styles.usageLabel}>{t('books.blocks.overview.usage.events')}</span>
                            </div>
                          </section>

                          <section className={`${styles.coreCard} ${styles.activityCard}`} aria-label={t('books.blocks.overview.activity.aria')}>
                            <span className={styles.coreLabel}>{t('books.blocks.overview.activity.label')}</span>
                            <span className={styles.activityValue} title={overviewStats.latestActivityHint}>
                              {overviewStats.latestActivityLabel}
                            </span>
                            <span className={styles.coreMeta} title={overviewStats.snapshotAbsolute}>
                              {t('books.blocks.overview.activity.snapshot', { relative: overviewStats.snapshotRelative })}
                            </span>
                          </section>
                        </div>
                        <div className={styles.insightsCard}>
                          <header className={styles.insightsHeader}>
                            <div className={styles.insightsTitles}>
                              <p className={styles.insightsTitle}>{t('books.blocks.overview.insights.title')}</p>
                            </div>
                            <div className={styles.insightsActions}>
                              <div className={styles.insightsSwitch} role="tablist" aria-label={t('books.blocks.overview.insights.switch.aria')}>
                                {insightViewDefs.map((tab) => (
                                  <button
                                    key={tab.key}
                                    type="button"
                                    role="tab"
                                    aria-selected={insightsView === tab.key}
                                    className={`${styles.insightsSwitchButton} ${insightsView === tab.key ? styles.insightsSwitchButtonActive : ''}`}
                                    onClick={() => setInsightsView(tab.key)}
                                  >
                                    {tab.label}
                                  </button>
                                ))}
                              </div>
                            </div>
                          </header>

                          <div className={styles.insightsBody}>
                            {insightsView === 'score' && (
                              overviewStats.scoreComponents.length > 0 ? (
                                <MaturityScoreBreakdown components={overviewStats.scoreComponents} />
                              ) : (
                                <p className={styles.sectionPlaceholder}>{t('books.blocks.overview.insights.score.empty')}</p>
                              )
                            )}

                            {insightsView === 'tasks' && (
                              <div className={styles.insightsSection}>
                                <div className={styles.insightsPanel}>
                                  <NextStepsChecklist
                                    snapshot={maturitySnapshot ?? null}
                                    isLoading={isMaturitySnapshotLoading}
                                    hideSummary
                                  />
                                </div>
                              </div>
                            )}

                            {insightsView === 'todos' && (
                              <div className={styles.insightsSection}>
                                <p className={styles.insightsSectionMeta}>{t('books.blocks.overview.insights.todos.meta')}</p>
                                {promotedTodos.length === 0 ? (
                                  <p className={styles.sectionPlaceholder}>{t('books.blocks.overview.insights.todos.empty')}</p>
                                ) : (
                                  <ul className={styles.todoPreviewList}>
                                    {promotedTodos.map((todo) => {
                                      const todoKey = `${todo.blockId}:${todo.itemId}`;
                                      const disabled = updateBlockContent.isPending && pendingTodoKey === todoKey;
                                      return (
                                        <li key={todoKey} className={styles.todoPreviewItem}>
                                          <label>
                                            <input
                                              type="checkbox"
                                              checked={todo.checked}
                                              disabled={disabled}
                                              onChange={(event) => {
                                                event.stopPropagation();
                                                void handleTogglePromotedTodo(todo.blockId, todo.itemId, event.target.checked);
                                              }}
                                            />
                                            <span className={styles.todoPreviewText}>{todo.text?.trim() ? todo.text : t('books.blocks.overview.insights.todos.placeholder')}</span>
                                          </label>
                                          <span className={styles.todoPreviewMeta}>
                                            {t('books.blocks.overview.insights.todos.blockLabel', {
                                              id: todo.blockId.slice(0, 8),
                                            })}
                                          </span>
                                        </li>
                                      );
                                    })}
                                  </ul>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      </section>
                    </article>
                  </section>
              </div>
            )}

            {activeTab === 'blocks' && (
              <div className={styles.layout}>
                <section className={styles.leftColumn}>
                  <div className={`${styles.sectionCard} ${styles.blocksTab}`}>
                    <BookEditorRoot
                      bookId={book.id}
                      onBlockCreated={() => {
                        void handleBlockLifecycle('created');
                      }}
                      onBlockDeleted={() => {
                        void handleBlockLifecycle('deleted');
                      }}
                    />
                  </div>
                </section>
              </div>
            )}

            {activeTab === 'timeline' && (
              <div className={styles.timelineTab}>
                <ChronicleTimelineList
                  bookId={book.id}
                  title={t('books.blocks.timeline.title')}
                  subtitle={t('books.blocks.timeline.subtitle')}
                />
              </div>
            )}

          </div>
        </div>
      </div>
      </div>
      {isBonusDialogOpen && (
        <div
          className={styles.bonusDialogOverlay}
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${bonusInputId}-title`}
        >
          <div
            className={styles.bonusDialog}
            onClick={(event) => event.stopPropagation()}
          >
            <header className={styles.bonusDialogHeader}>
              <p id={`${bonusInputId}-title`} className={styles.bonusDialogTitle}>
                {t('books.blocks.dialog.opsBonusTitle')}
              </p>
              <p className={styles.bonusDialogSubtitle}>{t('books.blocks.dialog.opsBonusSubtitle')}</p>
            </header>
            <div className={styles.bonusDialogBody}>
              <label htmlFor={bonusInputId} className={styles.bonusDialogLabel}>
                {t('books.blocks.dialog.opsBonusFieldLabel')}
              </label>
              <div className={styles.bonusInputRow}>
                <input
                  id={bonusInputId}
                  type="number"
                  min={-5}
                  max={5}
                  step={1}
                  value={bonusInput}
                  onChange={(event) => {
                    setBonusInput(event.target.value);
                    if (bonusError) {
                      setBonusError(null);
                    }
                  }}
                  className={styles.bonusInput}
                  disabled={bonusSubmitting}
                />
                <span className={styles.bonusInputSuffix}>%</span>
              </div>
              <p className={styles.bonusHint}>{t('books.blocks.dialog.opsBonusRangeHint')}</p>
              {bonusError && <p className={styles.bonusError}>{bonusError}</p>}
            </div>
            <div className={styles.bonusDialogActions}>
              <button
                type="button"
                className={styles.bonusCancelButton}
                onClick={handleCloseBonusDialog}
                disabled={bonusSubmitting}
              >
                {t('books.blocks.dialog.opsBonusCancel')}
              </button>
              <button
                type="button"
                className={styles.bonusApplyButton}
                onClick={handleSubmitBonusDialog}
                disabled={bonusSubmitting}
              >
                {bonusSubmitting ? t('books.blocks.shell.loading') : t('books.blocks.dialog.opsBonusApply')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
