'use client';

import React from 'react';
import { BadgeCheck, Blocks, ChevronDown, Layers3, ListChecks, Sparkles, Tags, Type } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import type { MaturityScoreComponentDto } from '@/features/maturity';
import { useI18n } from '@/i18n/useI18n';
import type { MessageKey } from '@/i18n/I18nContext';
import styles from './MaturityScoreBreakdown.module.css';

const FACTOR_LABEL_KEYS: Record<string, MessageKey> = {
  structure_title: 'books.blocks.overview.insights.score.factors.structureTitle',
  structure_summary: 'books.blocks.overview.insights.score.factors.structureSummary',
  structure_tags: 'books.blocks.overview.insights.score.factors.structureTags',
  structure_cover: 'books.blocks.overview.insights.score.factors.structureCover',
  structure_blocks: 'books.blocks.overview.insights.score.factors.structureBlocks',
  activity_recent_edit: 'books.blocks.overview.insights.score.factors.activityRecentEdit',
  activity_visits: 'books.blocks.overview.insights.score.factors.activityVisits',
  activity_todo_health: 'books.blocks.overview.insights.score.factors.activityTodoHealth',
  quality_block_variety: 'books.blocks.overview.insights.score.factors.qualityBlockVariety',
  quality_outline_depth: 'books.blocks.overview.insights.score.factors.qualityOutlineDepth',
  task_long_summary: 'books.blocks.overview.insights.score.factors.taskLongSummary',
  task_tag_landscape: 'books.blocks.overview.insights.score.factors.taskTagLandscape',
  task_outline_depth: 'books.blocks.overview.insights.score.factors.taskOutlineDepth',
  task_todo_zero: 'books.blocks.overview.insights.score.factors.taskTodoZero',
  manual_adjustment: 'books.blocks.overview.insights.score.factors.manualAdjustment',
};

const FACTOR_DETAIL_KEYS: Record<string, MessageKey> = {
  structure_title: 'books.blocks.overview.insights.score.factorDetails.structureTitle',
  structure_summary: 'books.blocks.overview.insights.score.factorDetails.structureSummary',
  structure_tags: 'books.blocks.overview.insights.score.factorDetails.structureTags',
  structure_cover: 'books.blocks.overview.insights.score.factorDetails.structureCover',
  structure_blocks: 'books.blocks.overview.insights.score.factorDetails.structureBlocks',
  activity_recent_edit: 'books.blocks.overview.insights.score.factorDetails.activityRecentEdit',
  activity_visits: 'books.blocks.overview.insights.score.factorDetails.activityVisits',
  activity_todo_health: 'books.blocks.overview.insights.score.factorDetails.activityTodoHealth',
  quality_block_variety: 'books.blocks.overview.insights.score.factorDetails.qualityBlockVariety',
  quality_outline_depth: 'books.blocks.overview.insights.score.factorDetails.qualityOutlineDepth',
  task_long_summary: 'books.blocks.overview.insights.score.factorDetails.taskLongSummary',
  task_tag_landscape: 'books.blocks.overview.insights.score.factorDetails.taskTagLandscape',
  task_outline_depth: 'books.blocks.overview.insights.score.factorDetails.taskOutlineDepth',
  task_todo_zero: 'books.blocks.overview.insights.score.factorDetails.taskTodoZero',
  manual_adjustment: 'books.blocks.overview.insights.score.factorDetails.manualAdjustment',
};

const FACTOR_ICONS: Record<string, LucideIcon> = {
  structure_title: Type,
  structure_summary: Layers3,
  structure_tags: Tags,
  structure_cover: BadgeCheck,
  structure_blocks: Blocks,
  activity_recent_edit: Sparkles,
  activity_visits: Sparkles,
  activity_todo_health: ListChecks,
  quality_block_variety: Layers3,
  quality_outline_depth: Blocks,
  task_long_summary: Layers3,
  task_tag_landscape: Tags,
  task_outline_depth: Blocks,
  task_todo_zero: ListChecks,
  manual_adjustment: BadgeCheck,
};

const formatFactorLabel = (factor: string, t: (key: MessageKey, vars?: Record<string, string | number>) => string): string => {
  const key = FACTOR_LABEL_KEYS[factor];
  if (key) {
    return t(key);
  }
  return factor.replace(/_/g, ' ').toUpperCase();
};

const formatFactorDetail = (
  factor: string,
  t: (key: MessageKey, vars?: Record<string, string | number>) => string,
  fallback?: string | null,
): string => {
  const key = FACTOR_DETAIL_KEYS[factor];
  if (key) {
    return t(key);
  }
  if (fallback && fallback.trim().length > 0) {
    return fallback;
  }
  return t('books.blocks.overview.insights.score.detailFallback');
};

const formatPoints = (points: number): string => {
  const value = Number.isFinite(points) ? points : 0;
  return `${value}%`;
};

const resolveIcon = (factor: string) => {
  return FACTOR_ICONS[factor] || Layers3;
};

type ScoreGroupKey = 'structure' | 'activity' | 'quality' | 'task' | 'manual' | 'other';

const SCORE_GROUP_KEYS: ScoreGroupKey[] = ['structure', 'activity', 'quality', 'task', 'manual', 'other'];

const resolveGroupKey = (factor: string): ScoreGroupKey => {
  if (factor.startsWith('structure_')) return 'structure';
  if (factor.startsWith('activity_')) return 'activity';
  if (factor.startsWith('quality_')) return 'quality';
  if (factor.startsWith('task_')) return 'task';
  if (factor === 'manual_adjustment') return 'manual';
  return 'other';
};

type ScoreItem = {
  id: string;
  label: string;
  detail: string;
  points: number;
  icon: LucideIcon;
};

interface ScoreGroup {
  key: ScoreGroupKey;
  title: string;
  total: number;
  items: ScoreItem[];
}

interface MaturityScoreBreakdownProps {
  components: MaturityScoreComponentDto[];
}

const EMPTY_COMPONENTS: MaturityScoreComponentDto[] = [];

export const MaturityScoreBreakdown: React.FC<MaturityScoreBreakdownProps> = ({ components }) => {
  const safeComponents = Array.isArray(components) ? components : EMPTY_COMPONENTS;
  const { t } = useI18n();

  const groups = React.useMemo<ScoreGroup[]>(() => {
    const lookup = SCORE_GROUP_KEYS.reduce<Record<ScoreGroupKey, ScoreGroup>>((acc, key) => {
      acc[key] = {
        key,
        title: t(`books.blocks.overview.score.groups.${key}` as MessageKey),
        total: 0,
        items: [],
      };
      return acc;
    }, {} as Record<ScoreGroupKey, ScoreGroup>);

    safeComponents.forEach((component, index) => {
      const key = resolveGroupKey(component.factor);
      const bucket = lookup[key] || lookup.other;
      const Icon = resolveIcon(component.factor);
      bucket.items.push({
        id: `${component.factor}-${index}`,
        label: formatFactorLabel(component.factor, t),
        detail: formatFactorDetail(component.factor, t, component.detail),
        points: component.points ?? 0,
        icon: Icon,
      });
      bucket.total += component.points ?? 0;
    });

    return SCORE_GROUP_KEYS.map((key) => lookup[key]).filter((group) => group.items.length > 0);
  }, [safeComponents, t]);

  const [collapsed, setCollapsed] = React.useState<Record<string, boolean>>({});

  React.useEffect(() => {
    setCollapsed((prev) => {
      let changed = false;
      const next: Record<string, boolean> = {};
      groups.forEach((group, index) => {
        if (Object.prototype.hasOwnProperty.call(prev, group.key)) {
          next[group.key] = prev[group.key];
        } else {
          next[group.key] = index >= 2;
          changed = true;
        }
      });
      if (Object.keys(prev).length !== Object.keys(next).length) {
        changed = true;
      }
      return changed ? next : prev;
    });
  }, [groups]);

  const totalPoints = React.useMemo(
    () => groups.reduce((sum, group) => sum + group.total, 0),
    [groups]
  );

  const handleToggle = (key: string) => {
    setCollapsed((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  if (groups.length === 0) {
    return null;
  }

  return (
    <section className={styles.card} aria-label={t('books.blocks.overview.insights.score.aria')}>
      <header className={styles.cardHeader}>
        <p className={styles.cardEyebrow}>{t('books.blocks.overview.insights.score.cardTitle')}</p>
        <span className={styles.cardScore}>{formatPoints(totalPoints)}</span>
      </header>

      <div className={styles.groups}>
        {groups.map((group) => {
          const isCollapsed = collapsed[group.key] ?? false;
          return (
            <div key={group.key} className={styles.group}>
              <button
                type="button"
                className={styles.groupHeader}
                aria-expanded={!isCollapsed}
                onClick={() => handleToggle(group.key)}
              >
                <div
                  className={`${styles.groupHeaderText} ${!isCollapsed ? styles.groupHeaderTextActive : ''}`.trim()}
                >
                  {group.title}
                </div>
                <span className={styles.groupPoints}>{formatPoints(group.total)}</span>
                <span className={styles.groupToggleIcon} aria-hidden="true">
                  <ChevronDown size={16} data-collapsed={isCollapsed} />
                </span>
              </button>

              {!isCollapsed && (
                <ul className={styles.itemList}>
                  {group.items.map((item) => {
                    const Icon = item.icon;
                    return (
                      <li key={item.id} className={styles.item}>
                        <span className={styles.icon} aria-hidden="true">
                          <Icon size={16} />
                        </span>
                        <div className={styles.body}>
                          <span className={styles.factor}>{item.label}</span>
                          <span className={styles.detail}>{item.detail}</span>
                        </div>
                        <span className={styles.points}>{formatPoints(item.points)}</span>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};

MaturityScoreBreakdown.displayName = 'MaturityScoreBreakdown';
