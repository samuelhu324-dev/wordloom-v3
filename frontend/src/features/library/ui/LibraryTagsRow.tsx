"use client";

import React from 'react';
import type { LibraryTagSummaryDto } from '@/entities/library';
import { DEFAULT_TAG_COLOR } from '@/features/library/constants';
import styles from './LibraryTagsRow.module.css';
import { useI18n } from '@/i18n/useI18n';

export type LibraryTagsRowSize = 'regular' | 'compact';

interface LibraryTagsRowProps {
  tags?: LibraryTagSummaryDto[];
  total?: number;
  maxVisible?: number;
  size?: LibraryTagsRowSize;
  placeholder?: string;
  className?: string;
}

export const LibraryTagsRow: React.FC<LibraryTagsRowProps> = ({
  tags = [],
  total,
  maxVisible = 3,
  size = 'regular',
  placeholder,
  className,
}) => {
  const { t } = useI18n();
  const resolvedPlaceholder = placeholder ?? t('libraries.tags.placeholder');
  const visible = tags.slice(0, maxVisible);
  const tagTotal = typeof total === 'number' ? total : tags.length;
  const remaining = Math.max(0, tagTotal - visible.length);
  const rowClassName = [styles.row, styles[size], className].filter(Boolean).join(' ');

  if (visible.length === 0 && remaining === 0) {
    return <div className={rowClassName}><span className={styles.placeholder}>{resolvedPlaceholder}</span></div>;
  }

  return (
    <div className={rowClassName} role="list">
      {visible.map((tag) => {
        const rawDescription = typeof tag.description === 'string' ? tag.description : undefined;
        const description = rawDescription?.trim();
        const ariaLabel = description
          ? t('libraries.tags.ariaWithDescription', { name: tag.name, description })
          : tag.name;
        const tooltipPayload = description || undefined;

        return (
          <span
            key={tag.id}
            role="listitem"
            className={styles.chip}
            title={description ? undefined : tag.name}
            aria-label={ariaLabel}
            data-tooltip={tooltipPayload}
            tabIndex={description ? 0 : undefined}
          >
            <span className={styles.swatch} style={{ backgroundColor: tag.color || DEFAULT_TAG_COLOR }} aria-hidden="true" />
            <span className={styles.label}>{tag.name}</span>
            {description && <span className={styles.visuallyHidden}>{description}</span>}
          </span>
        );
      })}
      {remaining > 0 && (
        <span
          className={`${styles.chip} ${styles.extraChip}`}
          title={t('libraries.tags.remaining', { count: remaining })}
          aria-label={t('libraries.tags.remaining', { count: remaining })}
        >
          +{remaining}
        </span>
      )}
    </div>
  );
};

export default LibraryTagsRow;
