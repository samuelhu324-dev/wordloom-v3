'use client';

import React from 'react';
import { AlertCircle, CheckCircle2, ChevronDown, Circle, Lock } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { BookMaturity } from '@/entities/book';
import type { MaturitySnapshotDto, TransitionTaskDto } from '@/features/maturity';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import styles from './NextStepsChecklist.module.css';

interface NextStepsChecklistProps {
  snapshot: MaturitySnapshotDto | null;
  isLoading?: boolean;
  hideSummary?: boolean;
}

const STAGE_LABEL_KEYS: Record<BookMaturity, MessageKey> = {
  seed: 'books.blocks.overview.stage.seed',
  growing: 'books.blocks.overview.stage.growing',
  stable: 'books.blocks.overview.stage.stable',
  legacy: 'books.blocks.overview.stage.legacy',
};

const STATUS_LABEL_KEYS: Record<TransitionTaskDto['status'], MessageKey> = {
  pending: 'books.blocks.overview.insights.tasks.status.pending',
  completed: 'books.blocks.overview.insights.tasks.status.completed',
  regressed: 'books.blocks.overview.insights.tasks.status.regressed',
  locked: 'books.blocks.overview.insights.tasks.status.locked',
};

const TASK_TITLE_KEYS: Record<string, MessageKey> = {
  long_summary: 'books.blocks.overview.insights.tasks.items.longSummary.title',
  tag_landscape: 'books.blocks.overview.insights.tasks.items.tagLandscape.title',
  outline_depth: 'books.blocks.overview.insights.tasks.items.outlineDepth.title',
  todo_zero: 'books.blocks.overview.insights.tasks.items.todoZero.title',
};

const TASK_DESCRIPTION_KEYS: Record<string, MessageKey> = {
  long_summary: 'books.blocks.overview.insights.tasks.items.longSummary.description',
  tag_landscape: 'books.blocks.overview.insights.tasks.items.tagLandscape.description',
  outline_depth: 'books.blocks.overview.insights.tasks.items.outlineDepth.description',
  todo_zero: 'books.blocks.overview.insights.tasks.items.todoZero.description',
};

const STATUS_ICONS: Record<TransitionTaskDto['status'], LucideIcon> = {
  pending: Circle,
  completed: CheckCircle2,
  regressed: AlertCircle,
  locked: Lock,
};

const formatTimestamp = (
  value: string | null | undefined,
  lang: string,
  t: (key: MessageKey, vars?: Record<string, string | number>) => string,
): string => {
  if (!value) return t('books.blocks.overview.insights.tasks.snapshotMissing');
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(lang, { hour12: false });
};

const formatStageLabel = (
  stage: BookMaturity | string | undefined,
  t: (key: MessageKey, vars?: Record<string, string | number>) => string,
): string => {
  if (!stage) return '';
  const normalized = typeof stage === 'string' ? stage.toLowerCase() : stage;
  const key = STAGE_LABEL_KEYS[normalized as BookMaturity];
  if (key) {
    return t(key);
  }
  return typeof stage === 'string' ? stage.toUpperCase() : '';
};

const formatStatusLabel = (
  status: TransitionTaskDto['status'],
  t: (key: MessageKey, vars?: Record<string, string | number>) => string,
): string => {
  const key = STATUS_LABEL_KEYS[status];
  if (key) {
    return t(key);
  }
  return status.toUpperCase();
};

const partitionTasks = (tasks: TransitionTaskDto[]) => {
  const completed: TransitionTaskDto[] = [];
  const locked: TransitionTaskDto[] = [];
  const active: TransitionTaskDto[] = [];

  tasks.forEach((task) => {
    if (task.status === 'completed') {
      completed.push(task);
      return;
    }
    if (task.status === 'locked') {
      locked.push(task);
      return;
    }
    active.push(task);
  });

  return { completed, locked, active, total: tasks.length } as const;
};

const renderTask = (
  task: TransitionTaskDto,
  t: (key: MessageKey, vars?: Record<string, string | number>) => string,
) => {
  const Icon = STATUS_ICONS[task.status] || Circle;
  const stageLabel = formatStageLabel(task.requiredStage, t);
  const statusLabel = formatStatusLabel(task.status, t);
  const titleKey = TASK_TITLE_KEYS[task.code];
  const descriptionKey = TASK_DESCRIPTION_KEYS[task.code];
  const title = titleKey ? t(titleKey) : task.title;
  const description = descriptionKey
    ? t(descriptionKey)
    : task.description || t('books.blocks.overview.insights.tasks.descriptionFallback');

  return (
    <li
      key={task.code}
      className={styles.item}
      data-status={task.status}
      data-done={task.status === 'completed'}
      role="listitem"
    >
      <span className={styles.statusIcon} aria-label={statusLabel} title={statusLabel}>
        <Icon size={18} />
      </span>
      <div className={styles.itemContent}>
        <div className={styles.itemHeader}>
          <strong className={styles.itemLabel}>{title}</strong>
          <div className={styles.itemMeta}>
            <span className={styles.taskWeight}>+{task.weight}</span>
            <span className={styles.stageChip}>{(stageLabel || task.requiredStage || '').toUpperCase()}</span>
          </div>
        </div>
        <p className={styles.itemDetail}>{description}</p>
        {task.status === 'locked' && (
          <p className={styles.itemHint}>
            {t('books.blocks.overview.insights.tasks.hint.locked', { stage: stageLabel })}
          </p>
        )}
        {task.status === 'regressed' && (
          <p className={styles.itemHint}>{t('books.blocks.overview.insights.tasks.hint.regressed')}</p>
        )}
      </div>
    </li>
  );
};

export const NextStepsChecklist: React.FC<NextStepsChecklistProps> = ({
  snapshot,
  isLoading = false,
  hideSummary = false,
}) => {
  const { t, lang } = useI18n();
  const tasks = React.useMemo(() => (Array.isArray(snapshot?.tasks) ? snapshot.tasks : []), [snapshot?.tasks]);
  const partitioned = React.useMemo(() => partitionTasks(tasks), [tasks]);
  const snapshotStage = snapshot?.stage;
  const stageLabel = snapshotStage ? formatStageLabel(snapshotStage, t) : undefined;
  const createdAtLabel = snapshot ? formatTimestamp(snapshot.createdAt, lang, t) : '';
  const [showCompleted, setShowCompleted] = React.useState(false);
  const [showActive, setShowActive] = React.useState(true);
  const activeListId = React.useId();

  if (isLoading) {
    return <p className={styles.placeholder}>{t('books.blocks.overview.insights.tasks.loading')}</p>;
  }

  if (!snapshot) {
    return <p className={styles.placeholder}>{t('books.blocks.overview.insights.tasks.noSnapshot')}</p>;
  }

  if (tasks.length === 0) {
    return (
      <p className={styles.placeholder}>
        {t('books.blocks.overview.insights.tasks.emptyForStage', {
          stage: stageLabel ?? snapshot.stage.toUpperCase(),
        })}
      </p>
    );
  }

  return (
    <div className={styles.wrapper} data-stage={snapshot.stage}>
      <div className={styles.sectionHeader}>
        <p className={styles.sectionLabel}>{t('books.blocks.overview.insights.tasks.title')}</p>
      </div>
      {!hideSummary && (
        <div className={styles.summaryRow}>
          <div className={styles.summaryRight}>
            <div className={styles.stageSummary}>
              <span className={styles.stageBadge}>{(stageLabel ?? snapshot.stage).toUpperCase()}</span>
              <p className={styles.summaryDescription}>
                {t('books.blocks.overview.insights.tasks.summaryStatus', {
                  completed: partitioned.completed.length,
                  total: partitioned.total,
                  active: partitioned.active.length,
                })}
              </p>
            </div>
            <div className={styles.summaryStats}>
              <span className={styles.countChip}>
                {t('books.blocks.overview.insights.tasks.summaryChip', { count: partitioned.total })}
              </span>
              <span className={styles.snapshotTime} title={createdAtLabel}>
                {t('books.blocks.overview.insights.tasks.snapshotLabel', { timestamp: createdAtLabel })}
              </span>
            </div>
          </div>
        </div>
      )}

      {partitioned.active.length > 0 && (
        <div className={styles.sectionGroup}>
          <div className={styles.listSectionHeader}>
            <button
              type="button"
              className={styles.listSectionButton}
              onClick={() => setShowActive((prev) => !prev)}
              aria-expanded={showActive}
              aria-controls={activeListId}
            >
              <span
                className={`${styles.listSectionLabel} ${showActive ? styles.listSectionLabelActive : ''}`.trim()}
              >
                {t('books.blocks.overview.insights.tasks.section.active')}
              </span>
              <ChevronDown
                size={14}
                className={styles.listSectionToggleIcon}
                data-open={showActive}
                aria-hidden="true"
              />
            </button>
            <span className={styles.listSectionMeta}>
              {t('books.blocks.overview.insights.tasks.itemsCount', { count: partitioned.active.length })}
            </span>
          </div>
          {showActive && (
            <ul className={styles.list} role="list" id={activeListId}>
              {partitioned.active.map((task) => renderTask(task, t))}
            </ul>
          )}
        </div>
      )}

      {partitioned.completed.length > 0 && (
        <div className={`${styles.sectionGroup} ${styles.completedSection}`}>
          <div className={styles.listSectionHeader}>
            <p className={styles.listSectionLabel}>{t('books.blocks.overview.insights.tasks.section.completed')}</p>
            <div className={styles.listSectionExtras}>
              <span className={styles.listSectionMeta}>
                {t('books.blocks.overview.insights.tasks.itemsCount', { count: partitioned.completed.length })}
              </span>
              <button
                type="button"
                className={styles.listSectionToggle}
                onClick={() => setShowCompleted((prev) => !prev)}
                aria-expanded={showCompleted}
              >
                <ChevronDown size={14} className={styles.listSectionToggleIcon} data-open={showCompleted} />
                {showCompleted
                  ? t('books.blocks.overview.insights.tasks.toggle.collapse')
                  : t('books.blocks.overview.insights.tasks.toggle.expand')}
              </button>
            </div>
          </div>
          {showCompleted && (
            <ul className={styles.list} role="list">
              {partitioned.completed.map((task) => renderTask(task, t))}
            </ul>
          )}
        </div>
      )}

      {partitioned.locked.length > 0 && (
        <div className={`${styles.sectionGroup} ${styles.lockedSection}`}>
          <div className={styles.listSectionHeader}>
            <p className={styles.listSectionLabel}>{t('books.blocks.overview.insights.tasks.section.locked')}</p>
            <span className={styles.listSectionMeta}>
              <Lock size={14} />
              {t('books.blocks.overview.insights.tasks.itemsCount', { count: partitioned.locked.length })}
            </span>
          </div>
          <ul className={`${styles.list} ${styles.lockedList}`} role="list">
            {partitioned.locked.map((task) => renderTask(task, t))}
          </ul>
        </div>
      )}
    </div>
  );
};

NextStepsChecklist.displayName = 'NextStepsChecklist';
